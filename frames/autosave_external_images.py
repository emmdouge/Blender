bl_info = {
	"name": "Auto-save external images",
	"author": "CoDEmanX",
	"version": (1, 0),
	"blender": (2, 67, 0),
	"location": "",
	"description": "Save image datablocks on saving .blend",
	"warning": "Works on external images only!",
	"wiki_url": "",
	"category": "System"}


import bpy

def save_external_images(dummy):
	for img in bpy.data.images:
		img.save()


def register():
	bpy.app.handlers.save_pre.append(save_external_images)


def unregister():
	bpy.app.handlers.save_pre.remove(save_external_images)


if __name__ == "__main__":
	register()
