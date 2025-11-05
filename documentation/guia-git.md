cuando se hagan cambios en el proyecto, se deben eliminar los archivos caché y logs para evitar conflictos con el control de versiones.
```bash
git rm -r --cached .
git commit -m "remove cached files and logs"
```
