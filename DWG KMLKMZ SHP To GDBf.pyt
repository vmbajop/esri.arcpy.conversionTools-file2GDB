# -*- coding: utf-8 -*-

import arcpy
import os
import zipfile
import shutil

# for Upload CAD
STANDARD_CAD_OUTPUT = ["Polygon_prjd", "Point_prjd", "Polyline_prjd", "MultiPatch_prjd"]
TARGET = {
    "polygon": "Polygon_prjd"
    "point"
}

# for Upload Shapefil
SHP_FILE_TYPES = [".shp", ".shx", ".dbf", ".prj"]
SRS_WGS_84_WEB_MERCATOR = 'PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],PARAMETER["Standard_Parallel_1",0.0],PARAMETER["Auxiliary_Sphere_Type",0.0],UNIT["Meter",1.0]]'

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "File to GDBf"
        self.alias = "FileToGDBf"

        # List of tool classes associated with this toolbox
        self.tools = [DWGtoGDBf, KML_KMZtoGDBf, SHPasZIPtoGDBf]


class DWGtoGDBf(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "CAD DWG to file GDB"
        self.description = "Convert CAD DWG File to file GDB"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        in_file = arcpy.Parameter( name='in_file',
                                        displayName='Input File',
                                        datatype='DEFile',
                                        direction='Input',
                                        parameterType='Required')
        in_file.filter.list = ["dwg"]

        in_coordsys = arcpy.Parameter( name='in_coordsys',
                                        displayName='Input Coordinate System',
                                        # datatype='GPCoordinateSystem',
                                        datatype="GPString",
                                        direction='Input',
                                        parameterType='Required')

        out_coordsys = arcpy.Parameter( name='out_coords',
                                        displayName='Output Coordinate System',
                                        # datatype='GPCoordinateSystem',
                                        datatype="GPString",
                                        direction='Input',
                                        parameterType='Required')

        out_tfwkid = arcpy.Parameter( name='out_tfwkid',
                                        displayName='Output TFWKID',
                                        datatype="GPString",
                                        direction='Input',
                                        parameterType='Required')

        out_points = arcpy.Parameter(name              = "Points_dwg"       ,
                                        displayName    = "Output Points"       ,
                                        direction      = "Output"              ,
                                        parameterType  = "Derived"             ,
                                        datatype       = "GPFeatureLayer"      ,
                                        multiValue     = "False"               )

        out_polylines = arcpy.Parameter(name           = "Polylines_dwg"    ,
                                        displayName    = "Output Polylines"    ,
                                        direction      = "Output"              ,
                                        parameterType  = "Derived"             ,
                                        datatype       = "GPFeatureLayer"      ,
                                        multiValue     = "False"               )

        out_polylgons = arcpy.Parameter(name           = "Polygons_dwg"    ,
                                        displayName    = "Output Polygons"    ,
                                        direction      = "Output"              ,
                                        parameterType  = "Derived"             ,
                                        datatype       = "GPFeatureLayer"      ,
                                        multiValue     = "False"               )

        out_multipatch = arcpy.Parameter(name          = "Multlipatch_dwg"   ,
                                        displayName    = "Output Multipatch"   ,
                                        direction      = "Output"              ,
                                        parameterType  = "Derived"             ,
                                        datatype       = "GPFeatureLayer"      ,
                                        multiValue     = "False"               )

        # Set defaults

        in_file.value = r"C:\edpr_gis_corporate\edpr_gps_utilities\sample_data\cad\20210618 - Le Truel.dwg"
        in_coordsys.value = "25830"
        out_coordsys.value = "102100"
        out_tfwkid.value = "1149"
        params = [in_file, in_coordsys, out_coordsys, out_tfwkid, out_points, out_polylines, out_polylgons, out_multipatch]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        in_file = parameters[0].valueAsText
        in_coordsys =  parameters[1].value
        out_coordsys = parameters[2].value
        out_tfwkid = parameters[3].value
        file_size = os.path.getsize(in_file)

        arcpy.AddMessage (f"File size detected: {file_size}")

        if file_size > 60000000:
            arcpy.AddError(f"File Size too large : {file_size}")
            exit()
        else:
            arcpy.AddMessage("Starting")

            arcpy.env.overwriteOutput = True
            arcpy.env.workspace = arcpy.env.scratchFolder

            arcpy.AddMessage(f"Input {in_file}")

            der_gdb = arcpy.management.CreateFileGDB(out_folder_path = arcpy.env.scratchFolder, out_name = "temp.gdb")

            arcpy.AddMessage(f"Created temporal GDB -----> {der_gdb}")

            srs = arcpy.SpatialReference(int(in_coordsys))
            # out_srs_tfwkid = arcpy.SpatialReference(int(out_tfwkid))
            out_srs = arcpy.SpatialReference(int(out_coordsys))

            der_feature_dataset = "temp"
            der_dataset = arcpy.conversion.CADToGeodatabase(input_cad_datasets = in_file,
                                                out_gdb_path = der_gdb,
                                                out_dataset_name = der_feature_dataset,
                                                reference_scale = 1000,
                                                spatial_reference = srs)

            arcpy.AddMessage(f"Converted {in_file} CADToGDB {der_gdb} in dataset {der_feature_dataset} in {der_dataset}")

            ident = "_dwg"
            walk = arcpy.da.Walk(der_gdb, datatype=['FeatureClass'])
            for dirpath, dirnames, filenames in walk:
                for in_filename in filenames:
                    out_name = os.path.join(str(der_gdb), in_filename) + ident
                    arcpy.AddMessage(out_name)
                    arcpy.management.Project(in_dataset = os.path.join(str(der_dataset), in_filename),
                        out_dataset = out_name,
                        out_coor_system = out_srs,
                        transform_method = out_tfwkid,
                        in_coor_system = srs
                    )
            
            output_points = os.path.join(str(der_gdb), "Point") + ident
            
            if arcpy.Exists(output_points):
                arcpy.AddMessage(f"Adding {output_points}")
                arcpy.SetParameter(4,output_points)
                arcpy.AddMessage(f"{output_points} added")
            else:
                arcpy.AddWarning("No point geometries found")            

            output_polylines = os.path.join(str(der_gdb), "Polyline") + ident
            
            if arcpy.Exists(output_polylines):
                arcpy.AddMessage(f"Adding {output_polylines}")
                arcpy.SetParameter(5,output_polylines)
                arcpy.AddMessage(f"{output_polylines} added")
            else:
                arcpy.AddWarning("No polylines geometries found")

            output_polygons = os.path.join(str(der_gdb), "Polygon") + ident
            
            if arcpy.Exists(output_polygons):
                arcpy.AddMessage(f"Adding {output_polygons}")
                arcpy.SetParameter(6,output_polygons)
                arcpy.AddMessage(f"{output_polygons} added")
            else:
                arcpy.AddWarning("No polygon geometries found")

            output_multipatch = os.path.join(str(der_gdb), "MultiPatch") + ident
            
            if arcpy.Exists(output_multipatch):
                arcpy.AddMessage(f"Adding {output_multipatch}")
                arcpy.SetParameter(7,output_multipatch)
                arcpy.AddMessage(f"{output_multipatch} added")
            else:
                arcpy.AddWarning("No multipatch geometries found")
        return

class KML_KMZtoGDBf(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "KML/KMZ to file GDB"
        self.description = "Convert KML/KMZ File to file Geodatabase"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        in_file = arcpy.Parameter( name='in_file',
                                        displayName='Input File',
                                        datatype='DEFile',
                                        direction='Input',
                                        parameterType='Required')
        in_file.filter.list = ["kml", "kmz"]

        out_points = arcpy.Parameter(name           = "Output_Points"    ,
                                        displayName    = "Output Points"    ,
                                        direction      = "Output"              ,
                                        parameterType  = "Derived"             ,
                                        datatype       = "GPFeatureLayer"      ,
                                        multiValue     = "False"               )

        out_polylines = arcpy.Parameter(name           = "Output_Polylines"    ,
                                        displayName    = "Output Polylines"    ,
                                        direction      = "Output"              ,
                                        parameterType  = "Derived"             ,
                                        datatype       = "GPFeatureLayer"      ,
                                        multiValue     = "False"               )

        out_polylgons = arcpy.Parameter(name           = "Output_Polygons"    ,
                                        displayName    = "Output Polygons"    ,
                                        direction      = "Output"              ,
                                        parameterType  = "Derived"             ,
                                        datatype       = "GPFeatureLayer"      ,
                                        multiValue     = "False"               )
        params = [in_file, out_points, out_polylines, out_polylgons]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        in_file = parameters[0].valueAsText

        output_layer, out_geodatabase = arcpy.conversion.KMLToLayer(in_kml_file = in_file,
                                                                    output_folder = arcpy.env.scratchFolder
                                                                     )

        output_points       = os.path.join(out_geodatabase, 'Placemarks', "Points")
        output_polylines    = os.path.join(out_geodatabase, 'Placemarks', "Polylines")
        output_polygons     = os.path.join(out_geodatabase, 'Placemarks', "Polygons")

        arcpy.AddMessage(f"Trying adding {output_points}")
        if arcpy.Exists(output_points):
            arcpy.AddMessage(f"  > Added {output_points}")
            arcpy.SetParameter(1,output_points)
        else:
            arcpy.SetParameter(1,"")


        arcpy.AddMessage(f"Trying adding {output_polylines}")
        if arcpy.Exists(output_polylines):
            arcpy.AddMessage(f"  > Added {output_polylines}")
            arcpy.SetParameter(2,output_polylines)
        else:
            arcpy.SetParameter(2,"")


        arcpy.AddMessage(f"Trying adding {output_polygons}")
        if arcpy.Exists(output_polygons):
            arcpy.AddMessage(f"  > Added {output_polygons}")
            arcpy.SetParameter(3,output_polygons)
        else:
            arcpy.SetParameter(3,"")

        return

class SHPasZIPtoGDBf(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "SHP as ZIP to GDBf"
        self.description = "Convert SHP as ZIP File to file Geodatabase"
        self.canRunInBackground = False
    
    def getParameterInfo(self):
        params = []
        # Parameter 0: Input ZIP file
        param0 = arcpy.Parameter(
            displayName="Input ZIP file",
            name="input_shapefile_zip",
            datatype="DEFile",
            parameterType="Required",
            direction="Input"
        )
        param0.filter.list = ["zip"]
        params.append(param0)

        # Parameter 1: Output coordinate system
        param1 = arcpy.Parameter(
            displayName="Output Coordinate System",
            name="out_coordsys",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
        )
        param1.value="3857"
        params.append(param1)

        # Parameter 2: Output Point Feature Class
        param2 = arcpy.Parameter(
            displayName="Output Point Feature Class",
            name="output_point",
            datatype="DEFeatureClass",
            parameterType="Derived",
            direction="Output"
        )
        params.append(param2)

        # Parameter 3: Output Polyline Feature Class
        param3 = arcpy.Parameter(
            displayName="Output Polyline Feature Class",
            name="output_polyline",
            datatype="DEFeatureClass",
            parameterType="Derived",
            direction="Output"
        )
        params.append(param3)

        # Parameter 4: Output Polygon Feature Class
        param4 = arcpy.Parameter(
            displayName="Output Polygon Feature Class",
            name="output_polygon",
            datatype="DEFeatureClass",
            parameterType="Derived",
            direction="Output"
        )
        params.append(param4)

        return params

    def isLicensed(self):
        """optional"""
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        # Input parameters
        input_shapefile_zip = parameters[0].valueAsText
        out_coordsys = parameters[1].valueAsText

        # Derived outputs
        output_point = parameters[2].valueAsText
        output_polyline = parameters[3].valueAsText
        output_polygon = parameters[4].valueAsText

        # Define helper functions
        def _check_geometry(featureclass):
            desc = arcpy.Describe(featureclass)
            return desc.shapeType

        def _check_file_types(folder_path, file_types):
            files_in_folder = os.listdir(folder_path)
            file_extensions_in_folder = {os.path.splitext(file)[1] for file in files_in_folder}
            return all(file_type in file_extensions_in_folder for file_type in file_types)

        def _unzip(zip_file, target_folder):
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(target_folder)

        # Processing
        try:
            scratch_folder = arcpy.env.scratchFolder
            shutil.copy(input_shapefile_zip, scratch_folder)
            basename = os.path.basename(input_shapefile_zip)
            copied_shapefile = os.path.join(scratch_folder, basename)
            _unzip(zip_file=copied_shapefile, target_folder=scratch_folder)

            if _check_file_types(folder_path=scratch_folder, file_types=[".shp", ".shx", ".dbf", ".prj"]):
                arcpy.env.workspace = scratch_folder
                list_feature_classes = arcpy.ListFeatureClasses()

                for feature_class in list_feature_classes:
                    project_featureclass = os.path.join(
                        arcpy.env.scratchGDB, os.path.splitext(feature_class)[0]
                    )
                    arcpy.management.Project(
                        in_dataset=feature_class,
                        out_dataset=project_featureclass,
                        out_coor_system=arcpy.SpatialReference(int(out_coordsys))
                    )

                arcpy.env.workspace = arcpy.env.scratchGDB
                list_feature_classes = arcpy.ListFeatureClasses()

                # Identificar puntos, líneas y polígonos
                output_point_fc, output_polyline_fc, output_polygon_fc = "", "", ""

                for feature_class in list_feature_classes:
                    geometry = _check_geometry(feature_class)
                    if geometry == "Point" and not output_point_fc:
                        output_point_fc = feature_class
                    elif geometry == "Polyline" and not output_polyline_fc:
                        output_polyline_fc = feature_class
                    elif geometry == "Polygon" and not output_polygon_fc:
                        output_polygon_fc = feature_class

                # Set outputs
                parameters[2].value = output_point_fc
                parameters[3].value = output_polyline_fc
                parameters[4].value = output_polygon_fc
            else:
                messages.addErrorMessage("El ZIP no contiene todos los archivos necesarios para un shapefile.")
                raise arcpy.ExecuteError("Faltan archivos requeridos del shapefile.")
        
        except Exception as e:
            messages.addErrorMessage(str(e))
            raise