from django.http import HttpResponse
from django.views.generic import TemplateView
from modules.ContextHandlers import instance
from django.template import RequestContext

class ChatView(TemplateView):
    template_name = 'ExampleApp/templates/pages/chat.html'
    route_path = 'chat/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use the ch instance to get the necessary data
        instance.add_message_object('assistant', 'Hello')
        messages = instance.get_context()
        # Add the data to the context dictionary
        context['messages'] = messages
        return context

    def post(self, request, *args, **kwargs):
        # Get the message and sender from the POST data
        message = request.POST.get('message')
        sender = request.POST.get('sender')
        # Use the ch instance to add the message to the conversation
        instance.add_message_object(sender, message)
        # Return a 200 OK response
        return HttpResponse(status=200)
