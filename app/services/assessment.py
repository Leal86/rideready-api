from dataclasses import dataclass
from typing import Literal


AssessmentLevel = Literal[
    "FAVORABLE",
    "CAUTION",
    "UNFAVORABLE",
]


@dataclass
class WeatherAssessment:
    level: AssessmentLevel
    reasons: list[str]


def assess_weather_conditions(
    *,
    activity_type: str,
    apparent_temperature: float,
    precipitation_probability: float,
    precipitation: float,
    wind_speed: float,
    wind_gusts: float,
) -> WeatherAssessment:
    caution_reasons = []
    unfavorable_reasons = []

    if apparent_temperature <= 0:
        unfavorable_reasons.append(
            "Temperatura aparente muito baixa."
        )
    elif apparent_temperature <= 5:
        caution_reasons.append(
            "Temperatura aparente baixa."
        )

    if apparent_temperature >= 35:
        unfavorable_reasons.append(
            "Temperatura aparente muito elevada."
        )
    elif apparent_temperature >= 30:
        caution_reasons.append(
            "Temperatura aparente elevada."
        )

    if precipitation_probability >= 80:
        unfavorable_reasons.append(
            "Probabilidade de precipitação muito elevada."
        )
    elif precipitation_probability >= 50:
        caution_reasons.append(
            "Probabilidade de precipitação elevada."
        )

    if precipitation >= 7.5:
        unfavorable_reasons.append(
            "Precipitação intensa prevista."
        )
    elif precipitation >= 2:
        caution_reasons.append(
            "Precipitação moderada prevista."
        )

    if activity_type == "CYCLING":
        caution_wind = 25
        unfavorable_wind = 40
    else:
        caution_wind = 30
        unfavorable_wind = 45

    if wind_speed >= unfavorable_wind:
        unfavorable_reasons.append(
            "Vento forte previsto para a atividade."
        )
    elif wind_speed >= caution_wind:
        caution_reasons.append(
            "Vento moderado a forte previsto."
        )

    if wind_gusts >= 60:
        unfavorable_reasons.append(
            "Rajadas de vento fortes previstas."
        )
    elif wind_gusts >= 40:
        caution_reasons.append(
            "Rajadas de vento relevantes previstas."
        )

    if unfavorable_reasons:
        return WeatherAssessment(
            level="UNFAVORABLE",
            reasons=unfavorable_reasons + caution_reasons,
        )

    if caution_reasons:
        return WeatherAssessment(
            level="CAUTION",
            reasons=caution_reasons,
        )

    return WeatherAssessment(
        level="FAVORABLE",
        reasons=[
            "Nenhuma condição meteorológica relevante de atenção foi identificada."
        ],
    )