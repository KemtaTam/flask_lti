from lti.tool_provider import ToolProvider
from .lti_validator import LTIRequestValidator

def check_request(request_info):
    """
    :request_info: dcit - must include ('headers', 'data', 'secret', 'url') 
    """
	#создание класса ToolProvider
    provider = ToolProvider.from_unpacked_request(
        secret=request_info.get('secret', None),
        params=request_info.get('data', {}),
        headers=request_info.get('headers', {}),
        url=request_info.get('url', '')
    )
	
	# is_valid_request - метод, который проводит валидацию запроса
	# внутри него происходит проверка сигнатуры (проверяем, совпадает ли хеш запроса, который в нем указан с тем кешем, который мы вычислили)
	# в LTIRequestValidator() содержится вся необходимая информация, которая требуется от нас
    #return provider.is_valid_request(LTIRequestValidator())
    return provider.is_valid_request(LTIRequestValidator())