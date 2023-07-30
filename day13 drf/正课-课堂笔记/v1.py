class Request:
	 def __init__(self, request, authenticators=None):
	 	self._request = request
	 	self.authenticators = authenticators or ()

	 



class APIView(View):
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES

	def get_authenticators(self):
		# [认证类的对象,认证类的对象,认证类的对象,认证类的对象,认证类的对象,]
        return [ auth() for auth in self.authentication_classes ]

    def initialize_request(self, request, *args, **kwargs):
        parser_context = self.get_parser_context(request)

        return Request(
            request,
            parsers=self.get_parsers(),
            authenticators=self.get_authenticators(), # [对象,对象,...]
            negotiator=self.get_content_negotiator(),
            parser_context=parser_context
        )

   def dispatch(self, request, *args, **kwargs):

   		# 请求的封装（django的request对象 + authenticators认证组件） -> 加载认证组件的过程
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request

        self.headers = self.default_response_headers  # deprecate?

        self.initial(request, *args, **kwargs)

        handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        response = handler(request, *args, **kwargs)

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response

class UserView(APIView):
	authentication_classes = [类1,类2,类3]
    def get(self, request):
        print(request.user, request.auth)
        return Response("UserView")



请求到来时，
	obj = UserView()
	obj.dispatch()