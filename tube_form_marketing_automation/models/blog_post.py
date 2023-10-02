

from odoo import _,api, fields, models, tools, SUPERUSER_ID
from odoo.http import request
import datetime
from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

class BlogPost(models.Model):
    _inherit = "blog.post"

    @api.model_create_multi
    def create(self, vals_list):
        res = super(BlogPost, self).create(vals_list)
        # Check if the blog is published
        for record in res:
            if record.is_published:
                record.workflow_3_blog_post_published_notification_send()
        return res


    def write(self, vals):
        res = super(BlogPost, self).write(vals)
        # Check if the blog is published
        if 'is_published' in vals and vals['is_published']:
            self.workflow_3_blog_post_published_notification_send()
        return res
    
    def workflow_3_blog_post_published_notification_send(self):
        for rec in self:
            blog_background_image_url = eval(rec.cover_properties).get('background-image')
            if 'none' != blog_background_image_url:
                blog_background_image_url = blog_background_image_url.split('(')[1].replace(')','')

            post_datetime_string = str(rec.post_date)
            try:
                post_input_datetime = datetime.strptime(post_datetime_string, "%Y-%m-%d %H:%M:%S")
            except:
                post_input_datetime = datetime.strptime(post_datetime_string, "%Y-%m-%d %H:%M:%S.%f")

            formatted_post_datetime = post_input_datetime.strftime("%b %d, %Y")
            for partner in rec.blog_id.message_partner_ids:
                blog_post_context = {
                    'blog_background_image_url' : blog_background_image_url,
                    'post_date' : formatted_post_datetime,
                    'email_to': partner.email
                }
                try:
                    template = request.env.ref('tube_form_marketing_automation.workflow_3_blog_notification_email_template')
                    template.with_context(**blog_post_context).send_mail(rec.id)
                except Exception as e:
                    _logger.error(f"Error sending email to subscribers while blog post published: {e}")
        return True


    def _check_for_publication(self, vals):
        '''
        Override this method and commented code to disable default blog published mail send process
        '''
        # if vals.get('is_published'):
        #     for post in self.filtered(lambda p: p.active):
        #         post.blog_id.message_post_with_view(
        #             'website_blog.blog_post_template_new_post',
        #             subject=post.name,
        #             values={'post': post},
        #             subtype_id=self.env['ir.model.data']._xmlid_to_res_id('website_blog.mt_blog_blog_published'))
        #     return True
        return False
