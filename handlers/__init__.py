from aiogram import Router
from .start import router as start_router
from .test import router as test_router
from .applications import router as applications_router
from .review import router as review_router
from .admin import router as admin_router
from .utils import router as utils_router
from .scheduler import router as scheduler_router

router = Router()
router.include_router(start_router)
router.include_router(test_router)
router.include_router(applications_router)
router.include_router(review_router)
router.include_router(admin_router)
router.include_router(utils_router)
router.include_router(scheduler_router)