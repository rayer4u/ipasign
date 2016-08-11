#coding:utf-8
from __future__ import print_function

from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse
from django.http import Http404
from django.http import HttpResponseRedirect
from django.core.files import File
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView
from os.path import abspath,dirname,join,basename,exists,splitext
from uuid import uuid4

import os
import json
import urlparse
import subprocess
import shutil
import re
import ipasign
import zipfile
import requests
import sys

from forms import UploadModelFileForm, ModelFileForm
from models import UpFile

@csrf_exempt  #for post out of html
def upload(request):
    if request.method == 'POST':
        form = UploadModelFileForm(request.POST, request.FILES)
        if form.is_valid():
            o = form.save(commit=False)
            
            #path检查
            path_rela = join(ipasign.PACKAGE_DIR, o.path)+'.ipa' #realative to MEDIA_ROOT
            path_full = join(settings.MEDIA_ROOT, path_rela)
            if exists(path_full):
                return HttpResponse(json.dumps({'err':'existed'}), content_type="application/json")
            if not exists(dirname(path_full)):
                os.makedirs(dirname(path_full))
                
            on = o.file.name  #origin file name

            current_uri = '%s://%s' % ('https' if request.is_secure() else 'http',
                             request.get_host())
            
            #证书检查
            cert,key = request.POST['certification'].split(':')
            if cert not in ipasign.CERTS or key not in ipasign.CERTS[cert]:
                return HttpResponse(json.dumps({'err':'wrong certification %s:%s'%(cert,key)}), content_type="application/json")
            #描述文件检查
			path_profile =join(ipasign.PROFILES_DIR, cert, request.POST['id'], request.POST['profile'])
			if not exists(path_profile):
				return HttpResponse(json.dumps({'err':'wrong profile path %s'%(path_profile)}), content_type="application/json")
			
            #保存
            o.from_ip = get_client_ip(request)
            o.status = 'uploaded'
            o.save()

            #解包
            unsignedapp = o.file.path
            signedipa = path_full

            tmpdir = uuid4().hex
            cmd_tar = r'mkdir %s;tar -xzf %s -C %s' % (tmpdir, unsignedapp, tmpdir)
            p = subprocess.Popen(cmd_tar, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=os.environ, shell=True)
            out, err = p.communicate()
            if len(err) > 0:
                o.status = 'untarfail'
                o.save()
                shutil.rmtree(tmpdir)
                return HttpResponse(json.dumps({'err':o.status}), content_type="application/json")

            #签名.remove tgz  ext
            tmpapp = join(tmpdir, splitext(on)[0])
#             cmd_sign = 'echo test > '+path_full
            cmd_sign = 'xcrun -sdk iphoneos RePackageApplication -v %s -o %s --sign "%s" --embed "%s"' \
                %(tmpapp, path_full, ipasign.CERTS[cert][key], join(ipasign.PROFILES_DIR, cert, request.POST['id'], request.POST['profile']))
            if 'entitlements' in request.POST:
                cmd_sign += ' --entitlements '+request.POST['entitlements'] 
            p = subprocess.Popen(cmd_sign, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            out, err = p.communicate()
            
            if len(err) > 0:
                print(err, file=sys.stderr)
                o.status = 'signfail'
                o.save()
                shutil.rmtree(tmpdir)
                return HttpResponse(json.dumps({'err':cmd_sign}), content_type="application/json")
            o.signed.name = path_rela  
            o.save()
            
            #pub
            files={key.encode('utf-8'):('', value[0].encode('utf-8')) for key,value in dict(request.POST).items()}
            path_signed_full =join(settings.MEDIA_ROOT, o.signed.path.encode('utf-8'))
            files['signed'] = (basename(path_signed_full), open(path_signed_full, 'rb'), 'application/iphone')
            if o.icons is not None:
                path_icons_full =join(settings.MEDIA_ROOT, o.icons.path.encode('utf-8'))
                files['icons'] = (basename(path_icons_full), open(path_icons_full, 'rb'), 'image/png')
            if o.iconb is not None:
                path_iconb_full =join(settings.MEDIA_ROOT, o.iconb.path.encode('utf-8'))
                files['iconb'] = (basename(path_iconb_full), open(path_iconb_full, 'rb'), 'image/png')
            files['from'] = o.from_ip
            ret = pub_post(files)
       
            o.status = 'success'
            o.save()
            shutil.rmtree(tmpdir)

            #保存列表
            form.save_m2m()

            if ret != '':
                result = {"url":ret}
            else:
                result = {'err':'signed but not publish success',
                          'url':urlparse.urljoin(current_uri, join(settings.MEDIA_URL, o.signed.url))}
        else:
            result = {'err':dict(form.errors)};
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        form = UploadModelFileForm()
        
    return render(request, 'upload.html', {'form': form})

class AllView(ListView):
    template_name="ipasign/upfile_list.html"
    paginate_by = 20
    
    def get_queryset(self):
        return UpFile.objects.order_by("-up_date")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(ListView, self).get_context_data(**kwargs)
        # Add in the publisher
        context['basedir'] = '%s://%s' % ('https' if self.request.is_secure() else 'http',
                             self.request.get_host())
        return context

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def pub_post(files):
    try:
        print("uploading publish...")
        print(files)
        print("")
        rep = requests.post(ipasign.PUBLISH_URL, files=files, verify=False)
        if rep.status_code == 200:
            ret = json.loads(rep.content)
            if 'url' in ret:
                print("success upload and sign. url is:")
                print(ret['url'])
                return ret['url']
            else:
                print(rep.content, file=sys.stderr)
        else:
            print(rep.content, file=sys.stderr)
    except Exception, e:
        print(e, file=sys.stderr)
        
    return ""
