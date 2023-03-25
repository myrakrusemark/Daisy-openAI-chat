from django.views.generic import TemplateView
import modules.ContextHandlers as ch

ch = ch.instance

class ChatView(TemplateView):
    template_name = 'ExampleApp/templates/pages/chat.html'
    route_path = 'chat/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use the ch instance to get the necessary data
        messages = ch.get_context()
        # Add the data to the context dictionary
        context['messages'] = messages
        return context