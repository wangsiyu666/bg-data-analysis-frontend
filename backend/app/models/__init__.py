# 让 Python 把这个目录当成包，并导出所有模型，把其他模型类导入到包级别，这样其他模块可以直接写 from app.models import Product 而不是 from app.models.product import Product。
#ORM（对象关系映射）：把数据库表（关系型）映射成 Python 类（对象）。
#好处：你可以用操作 Python 对象的方式（如 strategy.name = "新策略"）来操作数据库，不用写繁琐的 SQL。
from .product import Product
from .strategy import Strategy
from .script import Script
from .execution_plan import ExecutionPlan