# dlwinesd

dlwinesd is a small script/module to download Windows 10 and 11 ESDs directly from microsoft.com

## installation

`pip install dlwinesd`

## Usage
`import dlwinesd` to use it as a module, or run it from the command line, like:    
`./dlwinesd.py (--accept_eula|--get_eula) [--get_url] release edition arch lang`    
For example:    
`./dlwinesd.py --accept_eula 11 Enterprise x64 en-us`
