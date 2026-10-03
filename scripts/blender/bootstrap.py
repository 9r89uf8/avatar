"""Load pinned project-local MPFB without globally installing or saving preferences."""
import bpy,sys,types,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load_mpfb():
    for name,path in [('bl_ext',ROOT/'vendor'),('bl_ext.avatar',ROOT/'vendor/mpfb2/src')]:
        if name not in sys.modules:
            m=types.ModuleType(name);m.__path__=[str(path)];sys.modules[name]=m
    name='bl_ext.avatar.mpfb'
    spec=importlib.util.spec_from_file_location(name,ROOT/'vendor/mpfb2/src/mpfb/__init__.py',submodule_search_locations=[str(ROOT/'vendor/mpfb2/src/mpfb')])
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    bpy.context.preferences.addons.new().module=name
    module.register()
    module.set_preference('mpfb_second_root',str(ROOT/'vendor/assets'))
    from bl_ext.avatar.mpfb.services.locationservice import LocationService
    LocationService.update_second_root()
    return module
