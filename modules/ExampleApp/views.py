from django.http import HttpResponse
from django.views.generic import TemplateView
from django.template import RequestContext
from django.shortcuts import render
import json

import modules.ContextHandlers as ch
import modules.Chat as chat
import ModuleLoader as ml

class ChatView(TemplateView):
	template_name = 'ExampleApp/templates/pages/dashboard.html'
	route_path = 'chat/'
	#route_path = '/'


	def __init__(self):
		self.ch = ch.instance
		self.chat = chat.instance
		self.ml = ml.instance


	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		messages = self.ch.get_context()
		context['messages'] = messages
		available_modules = self.ml.get_available_modules()

		context['available_modules'] = available_modules

		return context

	def post(self, request, *args, **kwargs):
		print(request.POST)
		action = request.POST.get('action')
		message = request.POST.get('message')
		index = request.POST.get('index')
		role = request.POST.get('role')

		if action == 'delete':
			self.ch.delete_message_at_index(index)
			update_messages_section(request)
		elif action == 'edit':
			self.ch.update_message_at_index(message, index)
			update_messages_section(request)
		elif action == 'send':
			self.ch.add_message_object(role, message)
			response_text = self.chat.chat(self.ch.get_context_without_timestamp())
			self.ch.add_message_object("assistant", response_text)
			update_messages_section(request)
		elif action == 'append':
			self.ch.add_message_object(role, message)
			update_messages_section(request)
		elif action == 'module_update':
			module_name, new_state = message.split('-')
			if new_state == 'disabled':
				print(self.ml.enable_module(module_name))
			elif new_state == 'enabled':
				print(self.ml.disable_module(module_name))

	def update_messages_section(self, request):
		# Render the messages template with the updated context
		messages = self.ch.get_context()
		context = {'messages': messages}
		html = render(request, 'ExampleApp/templates/includes/chat-messages.html', context).content
		# Return the rendered template as the AJAX response
		return HttpResponse(html, content_type='text/html')
