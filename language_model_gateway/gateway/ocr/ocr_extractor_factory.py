from language_model_gateway.gateway.aws.aws_client_factory import AwsClientFactory
from language_model_gateway.gateway.ocr.aws_ocr_extractor import AwsOCRExtractor
from language_model_gateway.gateway.ocr.ocr_extractor import OCRExtractor


class OCRExtractorFactory:
    def __init__(self, *, aws_client_factory: AwsClientFactory) -> None:
        self.aws_client_factory: AwsClientFactory = aws_client_factory
        assert self.aws_client_factory is not None
        assert isinstance(self.aws_client_factory, AwsClientFactory)

    # noinspection PyMethodMayBeStatic
    def get(self, *, name: str) -> OCRExtractor:
        match name:
            case "aws":
                return AwsOCRExtractor(aws_client_factory=self.aws_client_factory)
            case _:
                raise ValueError(f"Unknown OCR extractor: {name}")
