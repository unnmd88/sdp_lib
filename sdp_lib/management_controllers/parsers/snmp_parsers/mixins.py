from sdp_lib.management_controllers.fields_names import FieldsNames


class StcipMixin:

    status_equipment = {
        '0': 'noInformation',
        '1': str(FieldsNames.three_light),
        '2': str(FieldsNames.power_up),
        '3': str(FieldsNames.dark),
        '4': str(FieldsNames.flash),
        '6': str(FieldsNames.all_red),
    }

    plan_source = {
        '1': 'trafficActuatedPlanSelectionCommand',
        '2': 'currentTrafficSituationCentral',
        '3': 'controlBlockOrInput',
        '4': 'manuallyFromWorkstation',
        '5': 'emergencyRoute',
        '6': 'currentTrafficSituation',
        '7': 'calendarClock',
        '8': 'controlBlockInLocal',
        '9': 'forcedByParameterBP40',
        '10': 'startUpPlan',
        '11': 'localPlan',
        '12': 'manualControlPlan',
    }

    @classmethod
    def get_status(cls, value: str) -> str | None:
        return cls.status_equipment.get(value)

    @classmethod
    def get_name_plan_source_from_value(cls, plan_source_val: str) -> str | None:
        return cls.plan_source.get(plan_source_val)


class Ug405Mixin:

    UTC_OPERATION_MODE = '3'

