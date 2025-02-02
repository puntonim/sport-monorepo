import csv
from pathlib import Path

CURR_DIR = Path(__file__).parent


def main():
    data = load_activities_from_csv()
    export_runs(data)


def load_activities_from_csv():
    data = []
    with open(
        CURR_DIR / "activities.csv",
        "r",
    ) as csvfile:
        reader = csv.reader(csvfile, delimiter="\t", quotechar="`")
        for row in reader:
            print(row)
            data.append(row)

    # TODO deleteme
    for datum in data:
        date = datum[0]
        type_ = datum[1]
        name = datum[2]
        moving_time_hours = datum[3]
        distance_km = datum[4]
        elevation_m = datum[5]
        descr = datum[6]
        print(date, type_, name, moving_time_hours, distance_km, elevation_m, descr)

    return data


def export_runs(data):
    with open(CURR_DIR / "run-activities.csv", "w") as fout:
        fout.write(
            "date\t"
            + "type\t"
            + "name\t"
            + "moving_time_hours\t"
            + "distance_km\t"
            + "elevation_m\t"
            + "has_tendinitis\n"
        )
        for datum in data:
            date = datum[0]
            type_ = datum[1]
            name = datum[2]
            moving_time_hours = datum[3]
            distance_km = datum[4]
            elevation_m = datum[5]
            descr = datum[6]

            if type_.lower() != "run":
                continue

            has_tendinitis = ""
            if "tend" in descr.lower() or "sole" in descr.lower():
                has_tendinitis = "tendinite"

            fout.write(
                f"{date};"
                + f"{type_};"
                + f"{name};"
                + f"{moving_time_hours};"
                + f"{distance_km};"
                + f"{elevation_m};"
                + f"{has_tendinitis}\n"
            )


if __name__ == "__main__":
    main()
