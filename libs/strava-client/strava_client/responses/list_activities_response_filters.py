import gis_utils

__all__ = [
    "FilterTypeError",
]


def does_title_contains_filter_match(
    title_contains_filter: str | None,
    activity_summary: dict,
) -> bool:
    """
    Check if the given text is included in the given activity summary `name` (title).

    Args:
        title_contains_filter: text (the match is case-insensitive).
        activity_summary: as returned by list_activities().
    """
    if title_contains_filter is None:
        return True

    # Validation.
    if not isinstance(title_contains_filter, str):
        raise FilterTypeError("title_contains must be string")

    # Match.
    if title_contains_filter.lower() not in activity_summary.get("name").lower():
        return False
    return True


def does_activity_type_filter_match(
    activity_type_filter: str | None,
    activity_summary: dict,
) -> bool:
    """
    Match the given activity type with the `type` or `sport_type` of the given activity.

    Args:
        activity_type_filter: all types described in https://github.com/puntonim/sport-monorepo/blob/main/libs/strava-db-models/strava_db_models/strava_db_models.py#L106.
        activity_summary: as returned by list_activities().
    """
    if activity_type_filter is None:
        return True

    # Validation.
    if not isinstance(activity_type_filter, str):
        raise FilterTypeError("activity_type must be string")

    # Match.
    if not (
        activity_summary.get("type").lower() == activity_type_filter.lower()
        or activity_summary.get("sport_type").lower() == activity_type_filter.lower()
    ):
        return False
    return True


def does_start_latlng_filter_match(
    start_latlng_filter: tuple[float, float, int] | tuple[float, float] | None,
    activity_summary: dict,
) -> bool:
    """
    Match the given location with the starting location of the given activity, within
     a certain distance.

    Args:
        start_latlng_filter: a tuple in the form (lat, lon, distance*).
         Distance is optional and its default value is 250 meters.
         Examples of lat and long:
           white_house = (38.898, -77.037)
           eiffel_tower = (48.858, 2.294)
           bsas = (-34.83333, -58.5166646)  # Ezeiza Airport (Buenos Aires, Argentina).
           paris = (49.0083899664, 2.53844117956)  # C. de Gaulle Airport (Paris, France).
           newport_ri = (41.49008, -71.312796)
           cleveland_oh = (41.499498, -81.695391)
        activity_summary: as returned by list_activities().
    """
    if start_latlng_filter is None:
        return True

    # Validation and parse.
    exc_msg = (
        "start_latlng_filter must be tuple[float, float, int] or tuple[float, float]"
    )
    if not isinstance(start_latlng_filter, tuple):
        raise FilterTypeError(exc_msg)
    try:
        lat_filter = start_latlng_filter[0]
        lon_filter = start_latlng_filter[1]
    except IndexError as exc:
        raise FilterTypeError(exc_msg) from exc
    try:
        dist_filter = start_latlng_filter[2]
    except IndexError:
        dist_filter = 250  # Default dist_filter: 250 meters.
    if (
        not isinstance(lat_filter, float)
        or not isinstance(lon_filter, float)
        or not isinstance(dist_filter, int)
    ):
        raise FilterTypeError(exc_msg)

    # Match.
    start_latlng = activity_summary.get("start_latlng")
    if not start_latlng:
        return False
    computed_distance = gis_utils.compute_euclidean_distance(
        start_latlng[0], start_latlng[1], lat_filter, lon_filter
    )
    if computed_distance * 1000 > dist_filter:
        return False
    return True


def does_end_latlng_filter_match(
    end_latlng_filter: tuple[float, float, int] | tuple[float, float] | None,
    activity_summary: dict,
) -> bool:
    """
    Match the given location with the ending location of an activity, within a certain
     distance.

    Args:
        end_latlng_filter: a tuple in the form (lat, lon, distance*).
         Distance is optional and its default value is 250 meters.
         Examples of lat and long:
           white_house = (38.898, -77.037)
           eiffel_tower = (48.858, 2.294)
           bsas = (-34.83333, -58.5166646)  # Ezeiza Airport (Buenos Aires, Argentina).
           paris = (49.0083899664, 2.53844117956)  # C. de Gaulle Airport (Paris, France).
           newport_ri = (41.49008, -71.312796)
           cleveland_oh = (41.499498, -81.695391)
        activity_summary: as returned by list_activities().
    """
    if end_latlng_filter is None:
        return True

    # Validation and parse.
    exc_msg = (
        "end_latlng_filter must be tuple[float, float, int] or tuple[float, float]"
    )
    if not isinstance(end_latlng_filter, tuple):
        raise FilterTypeError(exc_msg)
    try:
        lat_filter = end_latlng_filter[0]
        lon_filter = end_latlng_filter[1]
    except IndexError as exc:
        raise FilterTypeError(exc_msg) from exc
    try:
        dist_filter = end_latlng_filter[2]
    except IndexError:
        dist_filter = 250  # Default dist_filter: 250 meters.
    if (
        not isinstance(lat_filter, float)
        or not isinstance(lon_filter, float)
        or not isinstance(dist_filter, int)
    ):
        raise FilterTypeError(exc_msg)

    # Match.
    end_latlng = activity_summary.get("end_latlng")
    if not end_latlng:
        return False
    computed_distance = gis_utils.compute_euclidean_distance(
        end_latlng[0], end_latlng[1], lat_filter, lon_filter
    )
    if computed_distance * 1000 > dist_filter:
        return False
    return True


def does_location_visited_latlng_filter_match(
    location_visited_latlng_filter: (
        tuple[float, float, int] | tuple[float, float] | None
    ),
    activity_summary: dict,
) -> bool:
    """
    Check if the given location was visited in the given activity, within a certain
     distance.

    Args:
        location_visited_latlng_filter: a tuple in the form (lat, lon, distance*).
         Distance is optional and its default value is 250 meters.
         Examples of lat and long:
           white_house = (38.898, -77.037)
           eiffel_tower = (48.858, 2.294)
           bsas = (-34.83333, -58.5166646)  # Ezeiza Airport (Buenos Aires, Argentina).
           paris = (49.0083899664, 2.53844117956)  # C. de Gaulle Airport (Paris, France).
           newport_ri = (41.49008, -71.312796)
           cleveland_oh = (41.499498, -81.695391)
        activity_summary: as returned by list_activities().
    """
    if location_visited_latlng_filter is None:
        return True

    # Validation and parse.
    exc_msg = "location_visited_latlng_filter must be tuple[float, float, int] or tuple[float, float]"
    if not isinstance(location_visited_latlng_filter, tuple):
        raise FilterTypeError(exc_msg)
    try:
        lat_filter = location_visited_latlng_filter[0]
        lon_filter = location_visited_latlng_filter[1]
    except IndexError as exc:
        raise FilterTypeError(exc_msg) from exc
    try:
        dist_filter = location_visited_latlng_filter[2]
    except IndexError:
        dist_filter = 250  # Default dist_filter: 250 meters.
    if (
        not isinstance(lat_filter, float)
        or not isinstance(lon_filter, float)
        or not isinstance(dist_filter, int)
    ):
        raise FilterTypeError(exc_msg)

    # Match.
    polyline = activity_summary.get("map", {}).get("summary_polyline")
    if not polyline:
        return False
    coords = gis_utils.polyline_str_to_coords(polyline)
    for coord in coords:
        km = gis_utils.compute_euclidean_distance(
            coord[0],
            coord[1],
            lat_filter,
            lon_filter,
        )
        if km * 1000 <= dist_filter:
            return True
    return False


def does_distance_range_filter_match(
    distance_range_filter: str | None,
    activity_summary: dict,
) -> bool:
    """
    Match the given distance range type with the given activity.

    Args:
        distance_range_filter: a tuple of 2 ints to define the distance range inclusive,
         in meters. Eg. (9800, 10500) for a 10km run.
        activity_summary: as returned by list_activities().
    """
    if distance_range_filter is None:
        return True

    # Validation.
    exc_msg = "distance_range_filter must be tuple[int, int]"
    if not isinstance(distance_range_filter, tuple):
        raise FilterTypeError(exc_msg)
    try:
        range_a = distance_range_filter[0]
        range_b = distance_range_filter[1]
    except IndexError as exc:
        raise FilterTypeError(exc_msg) from exc
    if not isinstance(range_a, int) or not isinstance(range_b, int):
        raise FilterTypeError(exc_msg)

    # Match.
    distance = activity_summary.get("distance")
    if not distance:
        return False
    if distance < range_a or distance > range_b:
        return False
    return True


def does_elevation_gain_range_filter_match(
    elevation_gain_range_filter: str | None,
    activity_summary: dict,
) -> bool:
    """
    Match the given distance range type with the given activity.

    Args:
        elevation_gain_range_filter: a tuple of 2 ints to define the to elevation gain
         range inclusive, in meters. Eg. (600, 1000) for a ride.
        activity_summary: as returned by list_activities().
    """
    if elevation_gain_range_filter is None:
        return True

    # Validation.
    exc_msg = "elevation_gain_range_filter must be tuple[int, int]"
    if not isinstance(elevation_gain_range_filter, tuple):
        raise FilterTypeError(exc_msg)
    try:
        range_a = elevation_gain_range_filter[0]
        range_b = elevation_gain_range_filter[1]
    except IndexError as exc:
        raise FilterTypeError(exc_msg) from exc
    if not isinstance(range_a, int) or not isinstance(range_b, int):
        raise FilterTypeError(exc_msg)

    # Match.
    elevation_gain = activity_summary.get("total_elevation_gain")
    if not elevation_gain:
        return False
    if elevation_gain < range_a or elevation_gain > range_b:
        return False
    return True


class BaseListActivitiesResponseFilterException(Exception):
    pass


class FilterTypeError(BaseListActivitiesResponseFilterException): ...
