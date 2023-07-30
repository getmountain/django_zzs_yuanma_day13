



class OrderView(APIView):
    # authentication_classes = [...]
    permission_classes = [MyPermission1, MyPermission2, MyPermission3]

    def get(self, request):
        print(request.user, request.auth)
        self.dispatch()
        return Response({"status": True, "data": [11, 22, 33, 44]})
