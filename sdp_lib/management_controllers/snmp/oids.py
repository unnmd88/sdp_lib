import os
from enum import StrEnum
from dotenv import load_dotenv


load_dotenv()


class Oids(StrEnum):
    """
    В классе собраны оиды для ДК по протоколам STCIP и UG405
    """

    """ STCIP """
    # Command
    swarcoUTCTrafftechPhaseCommand = os.getenv('swarcoUTCTrafftechPhaseCommand')
    swarcoUTCCommandDark = os.getenv('swarcoUTCCommandDark')
    swarcoUTCCommandFlash = os.getenv('swarcoUTCCommandFlash')
    swarcoUTCTrafftechPlanCommand = os.getenv('swarcoUTCTrafftechPlanCommand')
    # Status
    swarcoUTCStatusEquipment = os.getenv('swarcoUTCStatusEquipment')
    swarcoUTCTrafftechPhaseStatus = os.getenv('swarcoUTCTrafftechPhaseStatus')
    swarcoUTCTrafftechPlanCurrent = os.getenv('swarcoUTCTrafftechPlanCurrent')
    swarcoUTCTrafftechPlanSource = os.getenv('swarcoUTCTrafftechPlanSource')
    swarcoSoftIOStatus = os.getenv('swarcoSoftIOStatus')
    swarcoUTCDetectorQty = os.getenv('swarcoUTCDetectorQty')
    swarcoUTCSignalGroupState = os.getenv('swarcoUTCSignalGroupState')
    swarcoUTCSignalGroupOffsetTime = os.getenv('swarcoUTCSignalGroupOffsetTime')
    swarcoUTCTrafftechFixedTimeStatus = os.getenv('swarcoUTCTrafftechFixedTimeStatus')
    swarcoUTCStatusMode = os.getenv('swarcoUTCStatusMode')
    potokS_UTCCommandAllRed = os.getenv('potokS_UTCCommandAllRed')
    potokS_UTCSetGetLocal = os.getenv('potokS_UTCSetGetLocal')
    potokS_UTCprohibitionManualPanel = os.getenv('potokS_UTCprohibitionManualPanel')
    potokS_UTCCommandRestartProgramm = os.getenv('potokS_UTCCommandRestartProgramm')
    # potokS_UTCStatusMode = os.getenv('potokS_UTCStatusMode')

    """ UG405 """
    # -- Control Bits --#
    utcType2Control = os.getenv('utcType2Control')
    utcControlLO = os.getenv('utcControlLO')
    utcControlFF = os.getenv('utcControlFF')
    utcControlTO = os.getenv('utcControlTO')
    utcControlFn = os.getenv('utcControlFn')
    # -- Reply Bits --#
    utcType2Reply = os.getenv('utcType2Reply')
    utcType2Version = os.getenv('utcType2Version')
    utcReplySiteID = os.getenv('utcReplySiteID')
    utcType2VendorID = os.getenv('utcType2VendorID')
    utcType2HardwareType = os.getenv('utcType2HardwareType')
    utcType2OperationModeTimeout = os.getenv('utcType2OperationModeTimeout')
    utcType2OperationMode = os.getenv('utcType2OperationMode')
    utcReplyGn = os.getenv('utcReplyGn')
    utcReplyFR = os.getenv('utcReplyFR')
    utcReplyDF = os.getenv('utcReplyDF')
    utcReplyMC = os.getenv('utcReplyMC')
    utcReplyCF = os.getenv('utcReplyCF')
    utcReplyVSn = os.getenv('utcReplyVSn')
    utcType2OutstationTime = os.getenv('utcType2OutstationTime')
    utcType2ScootDetectorCount = os.getenv('utcType2ScootDetectorCount')
    # -- Control Bits --#(Spec PotokP)
    potokP_utcControRestartProgramm = os.getenv('potokP_utcControRestartProgramm')
    # -- Reply Bits --#(Spec PotokP)
    potokP_utcReplyPlanStatus = os.getenv('potokP_utcReplyPlanStatus')
    potokP_utcReplyPlanSource = os.getenv('potokP_utcReplyPlanSource')
    potokP_utcReplyDarkStatus = os.getenv('potokP_utcReplyDarkStatus')
    potokP_utcReplyLocalAdaptiv = os.getenv('potokP_utcReplyLocalAdaptiv')
    potokP_utcReplyHardwareErr = os.getenv('potokP_utcReplyHardwareErr')
    potokP_utcReplySoftwareErr = os.getenv('potokP_utcReplySoftwareErr')
    potokP_utcReplyElectricalCircuitErr = os.getenv('potokP_utcReplyElectricalCircuitErr')


oids_state_swarco = (
    Oids.swarcoUTCTrafftechFixedTimeStatus,
    Oids.swarcoUTCTrafftechPlanSource,
    Oids.swarcoUTCStatusEquipment,
    Oids.swarcoUTCTrafftechPhaseStatus,
    Oids.swarcoUTCTrafftechPlanCurrent,
    Oids.swarcoUTCDetectorQty,
    Oids.swarcoSoftIOStatus
)

oids_state_potok_p = (
    Oids.utcType2OperationMode,
    Oids.potokP_utcReplyDarkStatus,
    Oids.utcReplyFR,
    Oids.utcReplyGn,
    Oids.potokP_utcReplyPlanStatus,
    Oids.potokP_utcReplyLocalAdaptiv,
    Oids.utcType2ScootDetectorCount,
    Oids.utcReplyDF,
    Oids.utcReplyMC,
)

oids_state_potok_s = (
    Oids.swarcoUTCStatusEquipment,
    Oids.swarcoUTCTrafftechPhaseStatus,
    Oids.swarcoUTCTrafftechPlanCurrent,
    Oids.swarcoUTCStatusMode,
    Oids.swarcoUTCDetectorQty,
)

oids_state_peek_ug405 = (
    # Не реализовано
)

oids_scn_required = {
        Oids.utcReplyGn, Oids.utcReplyFR, Oids.utcReplyDF, Oids.utcControlTO,
        Oids.utcControlFn, Oids.potokP_utcReplyPlanStatus, Oids.potokP_utcReplyPlanSource,
        Oids.potokP_utcReplyPlanSource, Oids.potokP_utcReplyDarkStatus,
        Oids.potokP_utcReplyLocalAdaptiv, Oids.potokP_utcReplyHardwareErr,
        Oids.potokP_utcReplySoftwareErr, Oids.potokP_utcReplyElectricalCircuitErr,
        Oids.utcReplyMC, Oids.utcReplyCF, Oids.utcReplyVSn, Oids.utcType2ScootDetectorCount
    }
