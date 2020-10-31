import os
import shutil
import time
import zipfile

if __name__ == "__main__":

	if os.path.isdir("build"):
		shutil.rmtree("build")
	if os.path.isdir("dist"):
		shutil.rmtree("dist")
	if os.path.isdir("provincerenamer"):
		shutil.rmtree("provincerenamer")
	os.system("pyinstaller provincerenamer.py --onefile")
	# ugly for permissions
	time.sleep(10)
	os.rename("dist", "provincerenamer")
	shutil.copy("LICENSE", "provincerenamer/LICENSE")
	shutil.copy("readme.md", "provincerenamer/readme.md")
	shutil.copy("namelist_sample.txt", "provincerenamer/namelist_sample.txt")

	zipf = zipfile.ZipFile("provincerenamer.zip", "w", zipfile.ZIP_DEFLATED)
	for root, dirs, files in os.walk("provincerenamer"):
		for file in files:
			zipf.write(os.path.join(root, file))
			
	zipf.close()