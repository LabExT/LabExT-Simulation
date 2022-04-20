
# shape=..., N=None, pos=..., size="auto", screensize="auto", title="vedo", bg="white", bg2=None, axes=None, sharecam=True, resetcam=True, interactive=None, offscreen=False, qtWidget=None, wxWidget=None, backend=None


from vedo import Plotter

class Plotter(Plotter):
    def __init__(self, withDoubleView = True):
        super().__init__(
            title="LabExT Simulation",
            shape=(1,2) if withDoubleView else (1,1),
            sharecam=False,
            size=(1080, 1440),
            axes=dict(
                xtitle='X [um]',
                ytitle='Y [um]',
                ztitle='Z [um]',
                numberOfDivisions=20,
                axesLineWidth= 2,
                gridLineWidth= 1,
                zxGrid2=True,
                yzGrid2=True, 
                xyPlaneColor='green7',
                xyGridColor='dg', 
                xyAlpha=0.1,
                xTitlePosition=0.5,
                xTitleJustify="top-center",
                yTitlePosition=0.5,
                yTitleJustify="top-center",
                zTitlePosition=0.5,
                zTitleJustify="top-center"))