@echo off
setlocal
chcp 65001 >nul
set "SRC=%~dp0"
set "DST=%USERPROFILE%\.zcode\skillslender-mcp"

echo [1/2] Copying skill payload -^> %DST%
if not exist "%DST%" mkdir "%DST%"
for %%D in (references scripts fragments nodes assets docs evals) do (
  if exist "%SRC%%%D" robocopy "%SRC%%%D" "%DST%%\%%D" /E /NFL /NDL /NJH /NJS >nul
)
for %%F in (SKILL.md INSTALL.md CHANGELOG.md) do (
  if exist "%SRC%%%F" copy /Y "%SRC%%%F" "%DST%%\%%F" >nul
)

echo [2/2] Next steps:
echo   1. Blender: Preferences -^> Add-ons -^> Install from Disk
echo      -^> assetsrickfly-mcp-bundlerickfly_mcp.py  (then enable it)
echo   2. Viewport N-panel -^> "Brickfly MCP for Blender" -^> Start MCP Server
echo   3. Register MCP server in your AI client (see INSTALL.md)
echo Done.
endlocal
