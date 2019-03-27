<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" indent="yes"/>
  
  <xsl:template match="insist_variables">
   <insist>
     <software_directory>
       <xsl:value-of select="root_directory"/>
       <xsl:value-of select="software_directory"/>
     </software_directory>
     <patients_directory>
       <xsl:value-of select="root_directory"/>
       <xsl:value-of select="patients_directory"/>
     </patients_directory>
     <generate_patients>
       <xsl:value-of select="root_directory"/>
       <xsl:value-of select="software_directory"/>
       <xsl:value-of select="virtual_patient_generation_dir"/>
       <xsl:value-of select="virtual_patient_generation_executable"/>
     </generate_patients>
     <generate_patients_flags>-f</generate_patients_flags>
     <generate_patients_xlsx>
       <xsl:value-of select="root_directory"/>
       <xsl:value-of select="software_directory"/>
       <xsl:value-of select="virtual_patient_generation_dir"/>
       <xsl:value-of select="virtual_patient_xsl"/>
     </generate_patients_xlsx>
     <generate_patients_prefix>
       <xsl:value-of select="root_directory"/>
       <xsl:value-of select="patients_directory"/>
       <xsl:value-of select="virtual_patient_prefix"/>
     </generate_patients_prefix>
     <generate_blood_flow_variables>
       <xsl:value-of select="root_directory"/>
       <xsl:value-of select="software_directory"/>
       <xsl:value-of select="virtual_patient_generation_dir"/>
       <xsl:value-of select="generate_blood_flow_variables"/>
     </generate_blood_flow_variables>
     <generate_perfusion_variables>
       <xsl:value-of select="root_directory"/>
       <xsl:value-of select="software_directory"/>
       <xsl:value-of select="virtual_patient_generation_dir"/>
       <xsl:value-of select="generate_perfusion_variables"/>
     </generate_perfusion_variables>
     <blood_flow_directory>
       <xsl:value-of select="root_directory"/>
       <xsl:value-of select="software_directory"/>
       <xsl:value-of select="blood_flow_software_directory"/>
     </blood_flow_directory>
     <blood_flow_executable>
       <xsl:value-of select="root_directory"/>
       <xsl:value-of select="software_directory"/>
       <xsl:value-of select="blood_flow_software_directory"/>
       <xsl:value-of select="bf_executable"/>
     </blood_flow_executable>
     <blood_flow_run_script>
       <xsl:value-of select="root_directory"/>
       <xsl:value-of select="software_directory"/>
       <xsl:value-of select="blood_flow_software_directory"/>
       <xsl:value-of select="bf_run_script"/>
     </blood_flow_run_script>
     <perfusion_directory>
       <xsl:value-of select="root_directory"/>
       <xsl:value-of select="software_directory"/>
       <xsl:value-of select="perfusion_software_directory"/>
     </perfusion_directory>
   </insist>
  </xsl:template>
</xsl:stylesheet>
