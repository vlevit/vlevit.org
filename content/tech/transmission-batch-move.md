/title: Пакетное перемещение торрентов в Transmission
/created: 2011-12-31 00:38+02:00
/tags: Transmission, bash, велосипед

Недавно я приобрёл бюджетный неттоп [ZOTAC ZBOX SD-ID12], который использую в
качестве домашнего сервера, wi-fi точки доступа и для хранения резервных копий
данных. Вот и решил я перенести на него все торренты. Пользовался я раньше
gtk+-версией [Transmission], а на «коробочку» я поставил, разумеется,
trasmsission-daemon. Необходимо изменились, и нужно было это как-то указать было
перенести все файлы и торренты. Пути к файлам, к сожалению, Transmission'у.
Собственно, тому, как это можно сделать, и посвящена данная заметка.

Transmission хранит все торренты в каталоге `~/.config/transmission/torrents`, а
всю дополнительную информацию, такую как место загрузки, приоритет, состояние и
прочее в `~/.config/transmission/resume`[^1]. Одному файлу \*.torrent в первом
каталоге соответствует один файл \*.resume во втором. Имена обоих файлов
определяются по шаблону `<имя торрента>.<хеш>.<расширение>`

[^1]: trasmsission-daemon хранит все файлы аналогичным образом в
      `~/.config/transmission-daemon`

Файлы \*.resume хранятся в том же формате, что и торрент-файлы — в [Bencode].
Формат бинарный, хоть и (тяжело) читаемый в текстовом виде. В нём могут
храниться целочисленные значения, массивы байт, списки и словари. Целочисленное
значение хранится как `i<число>e`, где <число> имеет десятичное представление в
виде строки, например `i935e`. Массив байт кодируется как
`<длина>:<содержимое>`, например, `4:data`. Списки и словари кодируются как
`l<содержимое>e` и `d<содержимое>e` соответственно. Подробнее рассматривать
формат не имеет смысла, так как нам этого вполне хватит.

resume-файл представляет из себя словарь свойств, описание которых можно найти
[тут] или в самом исходном файле [resume.c]. Нас интересует свойство
`destination`, которое и определяет место расположения данных. Очевидно, что
если просто заменить путь на новый, то файл повредится из-за несоответствия
длины старого и нового пути (если конечно нам не повезёт, и длина пути
совпадёт). При этом, если место хранения для всех торрентов одинаковое, то
пакетное перемещение сводится к тому, что нужно посчитать новую длину пути и
заменить участки всех resume-файлов с
`11:destination<old_length>/old/destination/path` на
`11:destination<new_length>/new/destination/path`. В случае, если значение
`destination` отличается, то необходимо пересчитывать длину пути для каждого
файла. Так как у меня именно этот случай, я создал небольшой shell-скрипт,
который делает это автоматически:

    :::bash
    #!/bin/bash
   
    CONFIG="${HOME}/.config/transmission"
    RESUME="${CONFIG}/resume"
    ORIG="${CONFIG}/resume.orig"
   
    if test $# != 2; then
        echo "Usage: $0 PATTERN REPLACEMENT"
        exit 1
    fi
   
    # escape comma in PATTERN and REPLACEMENT for use in sed
    PATTERN=$(sed -e "s=,=\\\\,=g" <<< "$1")
    REPLACEMENT=$(sed -e "s=,=\\\\,=g" <<< "$2")
   
    if test ! -d "${RESUME}"; then
        echo "error: $RESUME doesn't exist or is not a directory"
        exit 1
    fi
   
    if test -d "$ORIG"; then
        echo "error: $ORIG already exists"
        exit 1
    fi
   
    echo "copying $RESUME to $ORIG"
    cp -R "$RESUME" "$ORIG"
    test $? == 0 || exit 1
    echo "copying finished"
   
    echo "processing directory \"${ORIG}\"..."
   
    find "$RESUME" -type f -name "*.resume" | while read file
    do
        echo "processing $(basename "$file")"
   
        # calculate position of destination property
        dest=$(grep -aob "11:destination[0-9]\+" "$file")
        old_len=$(grep -o "[0-9]\+$" <<< "$dest")
        pos=$(grep -o "^[0-9]\+" <<< "$dest")
        end=$(($pos+14+${#old_len}+1+$old_len))
   
        # fetch the destination path, make the substitution
        old_path="$(head -c $end "$file"| tail -c $old_len)"
        new_path="$(sed -e "s,${PATTERN},${REPLACEMENT}," <<< "$old_path")"
   
        if test "$old_path" = "$new_path"; then
            echo "no need to update the file"
            continue
        fi
   
        # new path length in bytes, not characters
        new_len=$(expr length "$new_path")
        new_dest="11:destination${new_len}:${new_path}"
   
        # write temporary file and replace the original one
        tmpfile="${file}.tmp.$$"
        head -c $pos "$file" > "$tmpfile"
        echo -n "$new_dest" >> "$tmpfile"
        tail -c +$((${end}+1)) "$file" >> "$tmpfile"
        mv "$tmpfile" "$file"
   
        echo "file processed"
    done


Использовать скрипт так:

    transmission-batch-move ШАБЛОН ЗАМЕНА

где ШАБЛОН представляет собой регулярное выражение (как можно видеть,
оно в конечном итоге подставляется в `sed`). Например, если данные переместились
из `/home/olduser/olddata/torrents` в
`/home/user/data/torrents`, то скрипт можно запускать так:

    transmission-batch-move /home/olduser/olddata/ /home/user/data/

Скрипт создаст резервную копию каталога с resume-файлами и назовёт его
`resume.orig`. А resume-файлы по стандартному пути будут заменены на
новые. Скрипт укажет на те файлы, в которых замена не нужна (скорее
всего, это файлы, в свойстве `destination` которых не был найден ШАБЛОН).

Скрипт должен нормально работать с путями, которые содержат пробелы и
нелатинские символы. Но всё равно я рекомендую самостоятельно
удостоверится в правильном результате.

PS Завёл [аккаунт] на github. Этот скромный скрипт там пока [единственный].

PPS Новый год что ли? Хотелось бы, чтобы в новом году заметки появлялись
регулярно. Благо, идей для этого достаточно. Нужно лишь немного времени и
желания. В начале года было бы хорошо обновить статус [xatk] на [Google Code],
сделать релиз, написать заметку об изменениях. Но до этого ещё нужно
поработать... И конечно же я верю, что в следующем году блог, наконец-то,
оправдает своё название!

[ZOTAC ZBOX SD-ID12]: http://www.zotac.com/index.php?page=shop.product_details&flypage=flypage_images-SRW.tpl&product_id=331&category_id=75&option=com_virtuemart&Itemid=100167&lang=ua&vmcchk=1&Itemid=100167
[Transmission]: http://www.transmissionbt.com/
[Bencode]: http://en.wikipedia.org/wiki/Bencode
[тут]: https://trac.transmissionbt.com/wiki/ResumeFile
[resume.c]: https://trac.transmissionbt.com/browser/trunk/libtransmission/resume.c
[аккаунт]: https://github.com/vlevit
[единственный]: https://github.com/vlevit/transmission-batch-move
[xatk]: xatk-1
[Google Code]: http://code.google.com/p/xatk/
