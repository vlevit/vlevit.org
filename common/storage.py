from django.core.files.storage import FileSystemStorage


class OverwriteFileStorage(FileSystemStorage):

    def get_available_name(self, name):
        """
        Remove file under name `name` and return `name` back
        """
        if super(OverwriteFileStorage, self).exists(name):
                super(OverwriteFileStorage, self).delete(name)
        return name
