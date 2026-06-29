"""
Copyright (C) by ETHZ/SED

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

Module Description
------------------
The logReport module provides helper functions for the new sceewlog 
report generation (03.2026). The new report format includes the 
EEW preferred solution, point-source updates with epicenter, 
and finite-source updates with finder centroid.

Author: Thomas Planès, based on previous code by Yannik Behr and Fred Massin
"""

import os


def generateReport(event, evID, report_headers):
    """
    Generate a report for an event, including the preferred solution,
    point-source updates, and finite-source updates.
    """
    header_point_src, header_finite_src = report_headers
    updates = sorted(event['updates'].keys())
    u_pref = updates[-1] # get the latest update as the preferred solution
    org_pref = event['updates'][u_pref]
    
    point_src_updates, finite_src_updates = getUpdatesSolutions(event, updates, org_pref)
    report_point_src = header_point_src + "\n".join(point_src_updates)
    report_finite_src = ""
    if len(finite_src_updates) > 0:
        report_finite_src = header_finite_src + "\n".join(finite_src_updates) + "\n"
    report_pref = getFormattedPrefOrigin(org_pref, evID)
    report = "\n\n".join([report_pref, report_point_src, report_finite_src])
    
    event['diff'] = event['updates'][updates[0]]['difftopref'] # modified, first solution should be fastest by def
    event['type'] = org_pref['type']
    event['magnitude'] = org_pref['magnitude']
    event['region'] = org_pref['region']
    event['report'] = report
    return None


def getUpdatesSolutions(event, updates, org_pref):
    """
    Compile the point-source and finite-source solutions updates for the report.
    Save the max update magnitude for downstream email threshold checking 
    (done here to maintain legacy behavior). Also save the max likelihood for
    inclusion in email subject.
    """
    point_src_updates, finite_src_updates = [], []
    i_alert = 0

    max_mag = float('-inf')
    max_likelihood = 0.0
    for i_update, update in enumerate(updates):
        org_curr = event['updates'][update]
        if org_curr['eew'] is True:
            i_alert += 1
        difftime = org_curr['tsobject'] - org_pref['tsobject']  # diff between curr. origin and pref. origin creation time
        org_curr['difftopref'] = difftime.length() + org_pref['diff']
        max_mag = max(max_mag, org_curr['magnitude'])
        if 'likelihood' in org_curr:
            max_likelihood = max(max_likelihood, org_curr['likelihood'])
        simple_author = org_curr['author'].split('@')[0]  # Returns name before '@' if it exists, otherwise returns the whole string
        format_params_point_src = getFormatParamsPointSrc(org_curr, i_update, i_alert, simple_author)
        point_src_updates.append("|".join(format_params_point_src))

        format_params_finite_src = None
        if org_curr['centroid_lat'] is not None and org_curr['centroid_lon'] is not None:
            format_params_finite_src = getFormatParamsFiniteSource(org_curr, i_update, simple_author)
            finite_src_updates.append("|".join(format_params_finite_src))
    
    event['max_mag'] = max_mag
    event['max_likelihood'] = max_likelihood
    return point_src_updates, finite_src_updates


def getFormattedPrefOrigin(org_pref, evID):
    """
    Extract and format the preferred origin data for the report.
    """
    pref_params = (
            "EEW reference solution:\n",
            f"Time:   {org_pref['ot'].replace('Z', ' UTC')}",
            f"Lat:    {org_pref['lat']:.3f}",
            f"Lon:    {org_pref['lon']:.3f}",
            f"Depth:  {org_pref['depth']:.1f}",
            f"Mag:    {org_pref['magnitude']:.2f} {org_pref['type']}",
            f"Author: {org_pref['author']}",
            f"Evt ID: {evID}",
            f"Region: {org_pref['region']}" if org_pref['region'] else "Region: N/A"
    )
    return "\n".join(pref_params)


def getFormatParamsPointSrc(org, i_update, i_alert, simple_author):
    """
    Extract and format the point-source solution data for the current update.
    """
    format_params_point_src = (
        f"{i_update:>3d}",
        f"{org['difftopref']:>6.2f}",
        f"{org['type']:>4s}",
        f"{org['magnitude']:>5.2f}", 
        f"{org['lat']:>7.3f}", 
        f"{org['lon']:>8.3f}", 
        f"{org['depth']:>6.1f}", 
        f"{org['ot'][11:22]:>12s}", 
        f"{org['likelihood']:5.2f}" if 'likelihood' in org else " " * 5,
        f"{org['nstorg']:>3d}",
        f"{org['nstmag']:>3s}", 
        f" {org['ts'][11:22]:s}", 
        f" {simple_author[:9]:<9s}", 
        f"{org['diff']:>7.2f}",
        f"{i_alert:>4d}" if org['eew'] else " " * 4
    )
    return format_params_point_src


def getFormatParamsFiniteSource(org, i_update, simple_author):
    """
    Extract and format the finite-source solution data for the current update.
    """
    format_params_finite_src = (
        f"{i_update:>3d}",
        f"{org['difftopref']:6.2f}",
        f"{org['centroid_lat']:7.3f}", 
        f"{org['centroid_lon']:8.3f}", 
        f"{int(org['rupture-strike']):4d}" if 'rupture-strike' in org else " " * 4, 
        f"{org['rupture-length']:5.1f}" if 'rupture-length' in org else " " * 5, 
        f" {org['ts'][11:22]:s}", 
        f" {simple_author[:9]:<9s}"
    )
    return format_params_finite_src


def createReportHeaders():
    """
    Create the headers for the report tables.
    """
    point_src = (
        "Table 1: Point-source solutions\n",
        "                                                                | #St.  |                               | Alert ",
        "  #|dt-ref|Type|  Mag|   Lat |    Lon | Depth|  Orig time | Lik | Or| Ma|   Creation | Author   |dt-curr| App",
        "---------------------------------------------------------------------------------------------------------------\n"
    )
    finite_source = (
        "Table 2: Finite-source solutions\n",
        "          |   Centroid     |",
        "  #|dt-ref|   Lat |    Lon | Str| Len |   Creation | Author",
        "-----------------------------------------------------------\n"
    )
    return "\n".join(point_src), "\n".join(finite_source)


def saveReportToDisk(evID, report_directory, report):
    """
    Store the generated report on disk.
    """
    if not os.path.isdir(report_directory):
        os.makedirs(report_directory)
    with open(os.path.join(report_directory,
                            f"{evID.replace('/', '_')}_report.txt"), 'w') as f:
        f.writelines(report)


if __name__ == "__main__":
    raise SystemExit(
        "This module provides helper functions for sceewlog and is not meant to be run directly."
    )