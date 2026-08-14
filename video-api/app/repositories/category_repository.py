import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSession
from app.models import Category, Video


class CategoryRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self) -> list[Category]:
        result = await self.session.execute(select(Category))
        return result.scalars().all()


    async def get(self, id: uuid.UUID) -> Category:
        result = await self.session.execute(
            select(Category).where(Category.id == id)
        )
        return result.scalar_one_or_none()


    async def get_with_videos(self, id: uuid.UUID) -> Category | None:
        result = await self.session.execute(
            select(Category)
            .where(Category.id == id)
            .options(
                selectinload(Category.videos).load_only(Video.id, Video.title)
            )
        )

        return result.scalar_one_or_none()
    

    async def create(self, name: str, image_url: str | None = None) -> Category:
        new_category = Category(
            name=name,
            image_url=image_url
        )
        self.session.add(new_category)
        await self.session.flush()


    async def update(self, id: uuid.UUID, **data) -> Category | None:
        category = self.get(id)

        if not category:
            return None

        for key, value in data.items():
            setattr(category, key, value)

        await self.session.flush()
        return category


    async def delete(self, category: Category) -> None:
        self.session.delete(category)

    