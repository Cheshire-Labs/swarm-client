"""Device drivers for lab automation equipment.

This package provides:
- Abstract driver interfaces (interfaces.py)
- PyLabRobot backend wrappers (plr_wrappers.py)
- Simulation drivers for testing (sims.py)
- Teachpoint definitions for transporters (teachpoints.py)
"""

from .interfaces import (
    BaseDriver,
    IShakerDriver,
    ISealerDriver,
    ICentrifugeDriver,
    ITransporterDriver,
    IProtocolRunnerDriver,
    ILiquidHandlerDriver,
    IReaderDriver,
    IDelidderDriver,
    IStorageDriver,
    IPlateWasherDriver,
    IWasteDriver,
    ITempSettableDriver,
    ITempGettableDriver,
)

from .plr_wrappers import (
    PLRShakerBackendWrapper,
    PLRSealerBackendWrapper,
    PLRCentrifugeBackendWrapper,
    PLRTransporterBackendWrapper,
)

from .sims import (
    SimShakerDriver,
    SimSealerDriver,
    SimCentrifugeDriver,
    SimTransporterDriver,
    SimLiquidHandlerDriver,
    SimPlateWasherDriver,
    SimReaderDriver,
    SimDelidderDriver,
    SimStorageDriver,
    SimWasteDriver,
    SimDriver,
)

from .teachpoints import (
    Teachpoint,
    CartesianCoordinates,
    TeachpointsRegistry,
)

__all__ = [
    # Interfaces
    "BaseDriver",
    "IShakerDriver",
    "ISealerDriver",
    "ICentrifugeDriver",
    "ITransporterDriver",
    "IProtocolRunnerDriver",
    "ILiquidHandlerDriver",
    "IReaderDriver",
    "IDelidderDriver",
    "IStorageDriver",
    "IPlateWasherDriver",
    "IWasteDriver",
    "ITempSettableDriver",
    "ITempGettableDriver",
    # PLR Wrappers
    "PLRShakerBackendWrapper",
    "PLRSealerBackendWrapper",
    "PLRCentrifugeBackendWrapper",
    "PLRTransporterBackendWrapper",
    # Simulation Drivers
    "SimShakerDriver",
    "SimSealerDriver",
    "SimCentrifugeDriver",
    "SimTransporterDriver",
    "SimLiquidHandlerDriver",
    "SimPlateWasherDriver",
    "SimReaderDriver",
    "SimDelidderDriver",
    "SimStorageDriver",
    "SimWasteDriver",
    "SimDriver",
    # Teachpoints
    "Teachpoint",
    "CartesianCoordinates",
    "TeachpointsRegistry",
]
