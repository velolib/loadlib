from urllib.parse import urlparse
from urllib.request import urlopen
import validators as vld

class Validator():
    """Probably over-engineered URL validator class
    """
    @staticmethod
    def validate(*urls) -> None:
        for url in urls:
            
            if '//' not in url:
                url = '%s%s' % ('http://', url)
            
            # Method 1: urlparse
            method_1 = urlparse(url)
            if not all([method_1.scheme, method_1.netloc]):
                raise Exception(f'Exception when testing {url}, using Method 1')
            
            # Method 2: validators
            method_2 = vld.url(url) # type: ignore
            if not method_2:
                raise Exception(f'Exception when testing {url}, using Method 2')
            
            # Method 3: alloweds
            
        return
            
if __name__ == '__main__':
    Validator.validate('misode.github.io')