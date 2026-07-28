


# Series list
@router.get("/series", response_model=list[list_schema.SeriesListOut])
async def get_series_list(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Series))
    all_series = result.scalars().all()
    return all_series


# Series detail
@router.get("/series/{series_id}", response_model=list_schema.SeriesDetailOut)
async def get_series_detail(series_id: str, session: AsyncSession = Depends(get_db)):

    result = await session.execute(
        select(Series).where(Series.id == series_id)
    )
    series = result.scalar_one_or_none()

    if not series:
        raise HTTPException(status_code=404, detail=f"Video {series_id} not found!")

    return series

