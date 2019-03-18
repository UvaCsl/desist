<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:output method="xml" indent="yes"/>
  
  <xsl:template match="insist_variables">
   <insist>
     <software_directory><xsl:value-of select="root_directory"/><xsl:value-of select="software_directory"/></software_directory>
     <generate_patients><xsl:value-of select="root_directory"/><xsl:value-of select="software_directory"/><xsl:value-of select="virtual_patient_generation_dir"/><xsl:value-of select="virtual_patient_generation_executable"/></generate_patients>
     <generate_patients_flags>-f</generate_patients_flags>
     <generate_patients_xlsx><xsl:value-of select="root_directory"/><xsl:value-of select="software_directory"/><xsl:value-of select="virtual_patient_generation_dir"/><xsl:value-of select="virtual_patient_xsl"/></generate_patients_xlsx>
     <generate_patients_prefix><xsl:value-of select="root_directory"/><xsl:value-of select="patients_directory"/><xsl:value-of select="virtual_patient_prefix"/></generate_patients_prefix>
</insist>
  </xsl:template>
</xsl:stylesheet>
