from oauthlib.oauth1 import RequestValidator
from FDataBase import FDataBase

class LTIRequestValidator(RequestValidator):
	"""
	https://github.com/oauthlib/oauthlib/blob/master/oauthlib/oauth1/rfc5849/request_validator.py
	"""

#Все методы взяты из библиотеки oauthlib

	@property
	def client_key_length(self):	
		return 15, 30	#находится ли длина в таком промежутке

	@property
	def nonce_length(self):		
		return 20, 40   # len(nonce_from_moodle) = 32. default_return = (20, 30)

	@property	
	def enforce_ssl(self):		#применять ли ssl сертификат?
		return False		

#Методы, используемые для извлечения конфиденциальной информации из хранилища.
#возвращает секретный ключ клиента, чтобы проверить совпадает ли хэш, 
# который мы вычисляем на основе этого секрета, с тем хэшом, который был указан в запросе
	def get_client_secret(self, client_key, request):	
		return FDataBase().get_secret(client_key)	

#Методы, используемые для проверки/отмены входных параметров. 
	def validate_client_key(self, client_key, request):		#проверяет, а знаем ли мы клиента с таким ключом
		return FDataBase().is_key_valid(client_key)
		
#проверка, не было ли прислано ранее запросов с такими же временными метками
	def validate_timestamp_and_nonce(self, client_key, timestamp, nonce, request, request_token=None, access_token=None):
		if not FDataBase().has_timestamp_and_nonce(client_key, timestamp, nonce):
			# добавляем (timestamp, nonce) в данные клиента
			FDataBase().add_timestamp_and_nonce(client_key, timestamp, nonce)
			return True
		else:
			return False

#Чтобы предотвратить атаки по времени, необходимо не выходить раньше, 
# даже если ключ клиента или ключ владельца ресурса недействителен. 
# Вместо этого во время оставшегося процесса проверки следует использовать фиктивные значения.
#Фиктивный клиент используется, когда предоставляется недопустимый ключ клиента.
	def dummy_client(self):	
		return 'dummy_client'
