from rest_framework.schemas.openapi import AutoSchema


class DynamicResponseSerializerSchema(AutoSchema):
    """
    Override the response payload format to accurately
    represent the expected format in generated schemas.
    """
    def get_response_serializer(self, *args, **kwargs):
        serializer_cls = self.view.get_response_serializer()
        return serializer_cls()