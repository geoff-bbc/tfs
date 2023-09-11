

from odoo import _,api, fields, models, tools, SUPERUSER_ID
from odoo.http import request
import datetime
from datetime import datetime
from dateutil.relativedelta import relativedelta



class BlogPost(models.Model):
    _inherit = "blog.post"


    def workflow_3_blog_page_template_cron(self):
        today = datetime.now().date()
        blog_post_list = self.env["blog.post"].search([]).filtered(lambda a:a.post_date.strftime("%Y-%m-%d") == today.strftime("%Y-%m-%d"))

        for blog_post in blog_post_list:
            blog_background_image_url = eval(blog_post.cover_properties).get('background-image')
            if 'none' != blog_background_image_url:
                blog_background_image_url = blog_background_image_url.split('(')[1].replace(')','')

            post_datetime_string = str(blog_post.post_date)
            try:
                post_input_datetime = datetime.strptime(post_datetime_string, "%Y-%m-%d %H:%M:%S")
            except:
                post_input_datetime = datetime.strptime(post_datetime_string, "%Y-%m-%d %H:%M:%S.%f")

            formatted_post_datetime = post_input_datetime.strftime("%b %d, %Y")

            # Enter a contact email id
            email_to = ''

            blog_post_context = {
                'blog_background_image_url' : blog_background_image_url,
                'post_date' :formatted_post_datetime,
                'email_to': email_to if email_to else ''
            }

            contact_us_after_week_notify_email_template = self.env.ref(
                'tube_form_marketing_automation.workflow_3_blog_notification_email_template')
            contact_us_after_week_notify_email_template.with_context(**blog_post_context).send_mail(blog_post.id, force_send=True)



