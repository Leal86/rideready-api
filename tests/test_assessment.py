from app.services.assessment import assess_weather_conditions


def test_assessment_returns_favorable_for_normal_conditions():
    result = assess_weather_conditions(
        activity_type="WALKING",
        apparent_temperature=18,
        precipitation_probability=10,
        precipitation=0,
        wind_speed=12,
        wind_gusts=20,
    )

    assert result.level == "FAVORABLE"
    assert result.reasons == [
        "Nenhuma condição meteorológica relevante de atenção foi identificada."
    ]


def test_assessment_returns_caution_for_high_precipitation_probability():
    result = assess_weather_conditions(
        activity_type="RUNNING",
        apparent_temperature=18,
        precipitation_probability=65,
        precipitation=0,
        wind_speed=12,
        wind_gusts=20,
    )

    assert result.level == "CAUTION"
    assert "Probabilidade de precipitação elevada." in result.reasons


def test_assessment_returns_unfavorable_for_adverse_conditions():
    result = assess_weather_conditions(
        activity_type="CYCLING",
        apparent_temperature=18,
        precipitation_probability=85,
        precipitation=8,
        wind_speed=42,
        wind_gusts=65,
    )

    assert result.level == "UNFAVORABLE"

    assert "Probabilidade de precipitação muito elevada." in result.reasons
    assert "Precipitação intensa prevista." in result.reasons
    assert "Vento forte previsto para a atividade." in result.reasons
    assert "Rajadas de vento fortes previstas." in result.reasons


def test_cycling_uses_more_restrictive_wind_threshold():
    cycling_result = assess_weather_conditions(
        activity_type="CYCLING",
        apparent_temperature=18,
        precipitation_probability=10,
        precipitation=0,
        wind_speed=27,
        wind_gusts=20,
    )

    walking_result = assess_weather_conditions(
        activity_type="WALKING",
        apparent_temperature=18,
        precipitation_probability=10,
        precipitation=0,
        wind_speed=27,
        wind_gusts=20,
    )

    assert cycling_result.level == "CAUTION"
    assert walking_result.level == "FAVORABLE"