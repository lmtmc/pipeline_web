from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import re

class BaseRunfileEntry(BaseModel):
    obsnum: int
    s: str = Field(..., pattern="^[A-Za-z0-9]+$")

    @classmethod
    def validate_source_name(cls, v):
        if not v.isalnum():
            raise ValueError("Source name must be alphanumeric")
        return v
class RsrRunfileEntry(BaseRunfileEntry):
    x_lines: Optional[str] = None
    badcb: str = Field(..., pattern="^\d+/\d+$")
    srdp: int = Field(..., ge=0, le=1)
    admit: int = Field(..., ge=0, le=1)
    speczoom: Optional[str] = Field(None, pattern="^\d+,\d+$")
    bank: Optional[int] = Field(None, ge=0, le=1)
    xlines: Optional[str] = None
    jitter: int = Field(1, ge=0, le=1)
    badlags: Optional[str] = None
    shortlags: Optional[str] = None
    spike: int = Field(3, ge=0)
    linecheck: int = Field(0, ge=0, le=1)
    bandzoom: int = Field(5, ge=0, le=5)
    rthr: float = Field(0.01, ge=0, le=1)
    scthr: float = Field(0.01, ge=0, le=1)
    sgf: int = Field(0, ge=0)
    notch: int = Field(0, ge=0)
    blo: int = Field(1, ge=0)
    bandstats: int = Field(0, ge=0, le=1)

    @classmethod
    def validate_badcb(cls, v):
        parts = v.split('/')
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            raise ValueError("badcb must be in format 'int/int'")
        return v

    @classmethod
    def validate_xlines(cls, v):
        if v is not None and v != "":
            pairs = v.split(',')
            for pair in pairs:
                if not re.match(r'^\d+(\.\d+)?,\d+(\.\d+)?$', pair):
                    raise ValueError("xlines must be comma-separated freq,dfreq pairs")
        return v

    @classmethod
    def validate_shortlags(cls, v):
        if v is not None and v != "":
            if not re.match(r'^\d+(\.\d+)?,\d+(\.\d+)?$', v):
                raise ValueError("shortlags must be in format 'short_min,short_hi'")
        return v

    @classmethod
    def validate_speczoom(cls, v):
        if v is not None and v != "":
            if not re.match(r'^\d+(\.\d+)?,\d+(\.\d+)?$', v):
                raise ValueError("speczoom must be in format 'CENTER,HALF_WIDTH'")
        return v

    @classmethod
    def validate_sgf(cls, v):
        if v > 0 and v % 2 == 0:
            raise ValueError("sgf must be 0 or an odd number greater than 21")
        if v > 0 and v <= 21:
            raise ValueError("sgf must be 0 or greater than 21")
        return v

class SequoiaRunfileEntry(BaseRunfileEntry):
    beam: Optional[str] = Field(None, pattern="^[1-4]$")
    pixels: Optional[str] = None

    @classmethod
    def validate_pixels(cls, v):
        if v is not None:
            pixels = v.split(',')
            if not all(pixel.isdigit() and 0 <= int(pixel) <= 15 for pixel in pixels):
                raise ValueError("pixels must be comma-separated integers between 0 and 15")
        return v
def parse_line(line: str) -> dict:
    if not line.startswith("SLpipeline.sh"):
        raise ValueError("Line must start with 'SLpipeline.sh'")

    params = line.split()[1:]
    param_dict = {}
    for param in params:
        parts = param.split('=',1)
        if len(parts) != 2:
            raise ValueError(f"Invalid parameter format'{param}'")
        key, value = parts
        if key == '_s':  # Convert '_s' to 's' for Pydantic model
            key = 's'
        param_dict[key] = value
    return param_dict

def verify_runfile(lines, instrument) -> List[str]:
    errors = []
    for i, line in enumerate(lines):
        try:
            params = parse_line(line)
            if instrument == "rsr":
                model = RsrRunfileEntry
            elif instrument == "sequoia":
                model = SequoiaRunfileEntry
            else:
                raise ValueError(f"Unknown instrument {instrument}")
                continue
            print('params',params.keys(), 'model',model.__fields__.keys())
            # check for unkonwn fileds
            unknown_fields = set(params.keys()) - set(model.__fields__.keys())
            if unknown_fields:
                errors.append(f"Line {i+1}: Unknown fields {unknown_fields}")
            model(**params)
        except ValueError as e:
            errors.append(f"Line {i+1}: {str(e)}")
        except ValidationError as e:
            errors.append(f"Line {i+1}: {e}")
    return errors


