
class BaseThrottle:
    def allow_request(self, request, view):
        raise NotImplementedError('.allow_request() must be overridden')

    def get_ident(self, request):
        获取IP地址

    def wait(self):
        return None


class SimpleRateThrottle(BaseThrottle):
    cache = default_cache
    timer = time.time
    cache_format = 'throttle_%(scope)s_%(ident)s'
    scope = None
    THROTTLE_RATES = api_settings.DEFAULT_THROTTLE_RATES

    def __init__(self):
        if not getattr(self, 'rate', None):
            self.rate = self.get_rate()  # "5/m"  、  "3/h"

        # 5                60*60
        self.num_requests, self.duration = self.parse_rate(self.rate)

    def get_cache_key(self, request, view):
        raise NotImplementedError('.get_cache_key() must be overridden')

    def get_rate(self):
        if not getattr(self, 'scope', None):
            msg = ("You must set either `.scope` or `.rate` for '%s' throttle" %
                   self.__class__.__name__)
            raise ImproperlyConfigured(msg)

        try:
            # THROTTLE_RATES = {"XXX": "5/m"}   XXX
            return self.THROTTLE_RATES[self.scope]
        except KeyError:
            msg = "No default throttle rate set for '%s' scope" % self.scope
            raise ImproperlyConfigured(msg)

    def parse_rate(self, rate):
        # # "5/minite"  、  "3/hours"
        if rate is None:
            return (None, None)
        num, period = rate.split('/')
        num_requests = int(num)
        duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]
        return (num_requests, duration)

    def allow_request(self, request, view):
        if self.rate is None:
            return True

        # 获取用户的唯一标识
        self.key = self.get_cache_key(request, view)
        if self.key is None:
            return True

        # 历史访问记录 [16：46,16：45, 16:43, ]
        self.history = self.cache.get(self.key, [])


        self.now = self.timer()

        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()


        if len(self.history) >= self.num_requests:
            return self.throttle_failure()  # 超过限制

        return self.throttle_success() # 正常访问 True

    def throttle_success(self):
        self.history.insert(0, self.now)
        self.cache.set(self.key, self.history, self.duration)
        return True

    def throttle_failure(self):
        return False

    def wait(self):
        # [16：46, 16：45, 16:43, ]   60-4
        if self.history:
            remaining_duration = self.duration - (self.now - self.history[-1])   -> 还需要等待多久？
        else:
            remaining_duration = self.duration

        available_requests = self.num_requests - len(self.history) + 1
        if available_requests <= 0:
            return None

        return remaining_duration / float(available_requests)


class MyThrottle(SimpleRateThrottle):
    scope = "x2"
    # THROTTLE_RATES = {"x2": "3/m"}
    cache = default_cache

    def get_cache_key(self, request, view):
        if request.user:
            ident = request.user.pk  # 用户ID
        else:
            ident = self.get_ident(request)  # 获取请求用户IP（去request中找请求头）
        return self.cache_format % {'scope': self.scope, 'ident': ident}

-------------------------------------


class APIView(View):
    throttle_classes = 全局配置

    def get_throttles(self):
        # throttle_classes = [MyThrottle, ]
        # [ MyThrottle(),  ]
        return [throttle() for throttle in self.throttle_classes]

    def check_throttles(self, request):
        throttle_durations = [50,30,20 ]

        # 循环每个对象  -> allow_request到底是如何实现？

        for throttle in self.get_throttles():
            if not throttle.allow_request(request, self): # 超过评率限制
                throttle_durations.append( throttle.wait() )

        if throttle_durations:
            # Filter out `None` values which may happen in case of config / rate
            # changes, see #1438
            durations = [
                duration for duration in throttle_durations
                if duration is not None
            ]

            # 50
            duration = max(durations, default=None)
            self.throttled(request, duration)

    def throttled(self, request, wait):
        """
        If request is throttled, determine what kind of exception to raise.
        """
        raise exceptions.Throttled(wait)



    def initial(self, request, *args, **kwargs):
        
        self.perform_authentication(request)  # 认证组件的过程，循环执行每个authticate方法，失败抛出异常；request.user/auth
        self.check_permissions(request)       # 权限的校验   -> request.user/auth
        self.check_throttles(request)

   def dispatch(self, request, *args, **kwargs):
        
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.headers = self.default_response_headers  # deprecate?

        try:
            
            self.initial(request, *args, **kwargs)

            # 反射获取get/post/put/delete等方法
            handler = getattr(self, request.method.lower(),self.http_method_not_allowed)

            # 执行相应的方法
            response = handler(request, *args, **kwargs)

        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response



class OrderView(APIView):
    throttle_classes = [MyThrottle, ]
    permission_classes = [MyPermission1, MyPermission2, MyPermission3]

    def get(self, request):
        print(request.user, request.auth)
        
        return Response({"status": True, "data": [11, 22, 33, 44]})
