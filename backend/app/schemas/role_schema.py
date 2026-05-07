from pydantic import BaseModel


class RoleBase(BaseModel):
    name: str


class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: str
    
class RoleResponse(RoleBase):
    id: int

    class Config:
        from_attributes = True