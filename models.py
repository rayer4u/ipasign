# -*- coding: utf-8 -*-

import os,ipasign

from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from uuid import uuid4
from contenttyperestrictedfilefield import ContentTypeRestrictedFileField


def random_path(path):
    def wrapper(instance, filename):
        ext = ".".join(filename.split('.')[1:])
        # get filename
        if instance.pk:
            filename = '{0}.{1}'.format(instance.pk, ext)
        else:
            # set filename as random string
            filename = '{0}.{1}'.format(uuid4().hex, ext)
        # return the whole path to the file
        return os.path.join(path, filename)
    return wrapper

def icon_path(path):
    def wrapper(instance, filename):
        # get filename
        if instance.pk:
            ext = filename.split('.')[-1]
            filename = '{0}.{1}'.format(instance.pk, ext)
        else:
            # set filename with path
            filename = os.path.join(os.path.dirname(instance.path), filename)
        # return the whole path to the file
        return os.path.join(path, filename)
    return wrapper

class UpFile(models.Model):
    path    = models.CharField(max_length=200)   #上传路径
#     file    = models.FileField(upload_to=path_and_rename(ipasign.UPLOAD_DIR))
    file    = ContentTypeRestrictedFileField(content_types=['application/x-gtar'],
                                             max_upload_size=104857600,
                                             upload_to=random_path(ipasign.UPLOAD_DIR))  #上传的文件
    icons   = ContentTypeRestrictedFileField(content_types=['image/png'],
                                             max_upload_size=2621440,
                                             upload_to=icon_path(ipasign.PACKAGE_DIR))  #小图标
    iconb   = ContentTypeRestrictedFileField(content_types=['image/png'],
                                             max_upload_size=2621440,
                                             upload_to=icon_path(ipasign.PACKAGE_DIR))  #大图标
    signed  = models.FileField(upload_to=ipasign.PACKAGE_DIR)   #签名好的文件
    status  = models.CharField(max_length=10, blank=True)       #状态，uploaded，。。。
    user    = models.CharField(max_length=10, blank=False)      #上传的svn用户名
    label   = models.CharField(max_length=200, blank=True)      #标签
    up_date = models.DateTimeField('upload date', auto_now_add=True)    #上传的时间
    from_ip = models.GenericIPAddressField(blank=True, null=True)       #上传的ip

    def __unicode__(self):
        return self.path

# These two auto-delete files from filesystem when they are unneeded:
@receiver(models.signals.post_delete, sender=UpFile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """Deletes file from filesystem
    when corresponding `UpFile` object is deleted.
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)
    if instance.signed:
        if os.path.isfile(instance.signed.path):
            os.remove(instance.signed.path)

# @receiver(models.signals.pre_save, sender=UpFile)
# def auto_delete_file_on_change(sender, instance, **kwargs):
#     """Deletes file from filesystem
#     when corresponding `UpFile` object is changed.
#     """
#     if not instance.pk:
#         return False
# 
#     while True:
#         try:
#             old_file = UpFile.objects.get(pk=instance.pk).file
#         except UpFile.DoesNotExist:
#             break;
#     
#         new_file = instance.file
#         if not old_file == new_file:
#             if os.path.isfile(old_file.path):
#                 os.remove(old_file.path)
#                 
#         break
#     
#     while True:
#         try:
#             old_file = UpFile.objects.get(pk=instance.pk).signed
#         except UpFile.DoesNotExist:
#             break;
#     
#         new_file = instance.signed
#         if not old_file == new_file:
#             if os.path.isfile(old_file.path):
#                 os.remove(old_file.path)
#                 
#         break
