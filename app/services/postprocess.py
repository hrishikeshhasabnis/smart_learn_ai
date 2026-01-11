from typing import Set
from app.schemas.itinerary import Itinerary, ItineraryDay, ItineraryItem

ALLOWED_FREE = {"FREE_FULL", "FREE_AUDIT"}  # policy: adjust as you like

def enforce_constraints(
    plan: Itinerary,
    max_links_per_day: int,
    max_total_links: int,
    free_only: bool = True,
) -> Itinerary:
    seen: Set[str] = set()
    total = 0
    new_days: list[ItineraryDay] = []

    for d in plan.itinerary:
        items: list[ItineraryItem] = []
        for it in d.items:
            if total >= max_total_links:
                break

            url_str = str(it.url)
            if url_str in seen:
                continue

            if free_only and it.free_label not in ALLOWED_FREE:
                continue

            items.append(it)
            seen.add(url_str)
            total += 1

            if len(items) >= max_links_per_day:
                break

        new_days.append(ItineraryDay(day=d.day, objective=d.objective, items=items))
        if total >= max_total_links:
            break

    plan.itinerary = new_days
    return plan
