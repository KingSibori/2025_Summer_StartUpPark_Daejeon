from pydantic import BaseModel

class TextRequest(BaseModel):
    text: str

class WeatherRequest(BaseModel):
    location: str
