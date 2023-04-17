from django.http import HttpResponse
from django.views.generic import TemplateView
from django.shortcuts import render
import logging


class Dashboard(TemplateView):
	template_name = 'Dashboard_WebConfigDjango/templates/pages/dashboard.html'
	route_path = 'dashboard/'
	#route_path = '/'


	def __init__(self):
		print("DASHBOARD")
		self.ml = None
		self.ch = None
		self.chat = None


		self.context = {}


	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		
		from modules.WebConfigDjango.WebConfigDjango import GLOBAL_ML, GLOBAL_CH, GLOBAL_CHAT
		self.ml = GLOBAL_ML
		self.ch = GLOBAL_CH
		self.chat = GLOBAL_CHAT

		print(self.ml)

		messages = self.ch.get_context()
		self.context['messages'] = messages

		self.context['available_modules'] = self.ml.get_available_modules()
		return self.context

	def post(self, request, *args, **kwargs):
		logging.debug(request.POST)
		action = request.POST.get('action')
		message = request.POST.get('message')
		index = request.POST.get('index')
		role = request.POST.get('role')

		#Chat actions
		if action == 'delete':
			self.ch.delete_message_at_index(index)
			return self.update_messages_section(request)
		elif action == 'edit':
			self.ch.update_message_at_index(message, index)
			return self.update_messages_section(request)
		elif action == 'send':
			self.ch.add_message_object(role, message)
			response_text = self.chat.chat(self.ch.get_context_without_timestamp())
			self.ch.add_message_object("assistant", response_text)
			return self.update_messages_section(request)
		elif action == 'append':
			self.ch.add_message_object(role, message)
			return self.update_messages_section(request)

		#Module actions
		elif action == 'module_update':
			module_name, new_state = message.split('-')
			if new_state == 'disabled': #Enable module
				self.context['available_modules'] = self.ml.enable_module(module_name)
			elif new_state == 'enabled': #Disable module
				self.context['available_modules'] = self.ml.disable_module(module_name)
			elif new_state == 'update': #Disable module
				self.context['available_modules'] = self.ml.get_available_modules()

			return self.update_plugins_section(request)



	def update_messages_section(self, request):
		# Render the messages template with the updated context
		self.context['messages'] = self.ch.get_context()
		html = render(request, 'Dashboard_WebConfigDjango/templates/includes/chat-messages.html', self.context).content
		# Return the rendered template as the AJAX response
		return HttpResponse(html, content_type='text/html')

	def update_plugins_section(self, request):
		# Render the messages template with the updated context
		html = render(request, 'Dashboard_WebConfigDjango/templates/includes/modules.html', self.context).content
		# Return the rendered template as the AJAX response
		return HttpResponse(html, content_type='text/html')
