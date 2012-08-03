# Copyright 2011 Concentric Sky, Inc. 
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.template import Template, Context, loader, TemplateDoesNotExist
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template.defaultfilters import striptags
from basic_models import models as basic_models



class EmailTemplate(basic_models.SlugModel):
    base_template = models.CharField(max_length=1024, blank=True, help_text="If present, the name of a django template.<br/> The body field will be present as the 'email_body' context variable")
    subject = models.CharField(max_length=1024)
    from_address = models.CharField(max_length=1024, blank=True, null=True, help_text="Specify as: 'Full Name &lt;email@address>'<br/>Defaults to: 'no-reply@site.domain'")
    body = models.TextField(default='')
    txt_body = models.TextField(blank=True, null=True, help_text="If present, use as the plain-text body")

    def render(self, context):
        if self.base_template:
            try: 
                t = loader.get_template(self.base_template)
                context.update({'email_body': self._render_from_string(self.body, context)})
                return t.render(Context(context))
            except TemplateDoesNotExist as e:
                pass
        return self._render_from_string(self.body, context)

    def render_txt(self, context):
        if self.txt_body:
            return self._render_from_string(self.txt_body, context)
    
    def visible_from_address(self):
        if self.from_address:
            return self.from_address
        site = Site.objects.get_current()
        if site.name:
            # This is causing a BotoServerError: 'Domain contains illegal character'
            return '%s <no-reply@%s>' % (site.name, site.domain)
        else:
            return 'no-reply@%s' % site.domain
    
    def send(self, to_address, context={}, attachments=None, headers=None):
        html_body = self.render(context)
        text_body = self.render_txt(context) or striptags(html_body)
       
        subject = self._render_from_string(self.subject, context)
        if isinstance(to_address, (str,unicode)):
            to_address = (to_address,)
        msg = EmailMultiAlternatives(subject, text_body, self.visible_from_address(), to_address, headers=headers)
        msg.attach_alternative(html_body, "text/html")

        if attachments is not None:
            for attach in attachments:
                msg.attach(*attach)

        return msg.send()

    def _render_from_string(self, s, context):
        t = Template(s)
        return t.render(Context(context)) 

    @staticmethod
    def send_template(slug, to_address, context={}, attachments=None, headers=None):
        from emailtemplates.utils import send_email_template
        return send_email_template(slug, to_address, context=context, attachments=attachments, headers=headers)

