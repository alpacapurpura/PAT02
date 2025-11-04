cuando se hagan cambios en el proyecto, se deben eliminar los archivos caché y logs para evitar conflictos con el control de versiones.
```bash
git rm -r --cached .
git commit -m "remove cached files and logs"
```

Cuando el reposotorio pesa demasiado, se puede compactar el repositorio para reducir su tamaño y mejorar el rendimiento. Para ello, se puede usar el siguiente comando:
```bash
git gc --aggressive 
```
