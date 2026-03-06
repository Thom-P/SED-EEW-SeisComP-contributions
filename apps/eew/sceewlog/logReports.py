## todo main here, and new lookup in garbage collector in sceewlog.py

def generateReport(self, evID):
        """
        Generate a report for an event, write it to disk and optionally send
        it as an email.
        """
        seiscomp.logging.info("Generating report for event %s " % evID)

        prefindex = sorted(self.event_dict[evID]['updates'].keys())[-1]
        #report_point_src = self.report_head_point_src
        #report_finite_fault = self.report_head_finite_fault
        point_src_updates = []
        finite_fault_updates = []    

        threshold_exceeded = False
        self.event_dict[evID]['diff'] = 9999
        for _i in sorted(self.event_dict[evID]['updates'].keys()):
            ed = self.event_dict[evID]['updates'][_i]
            mag = ed['magnitude']
            if ( mag > self.magThresh and 
                ( self.email_sendForAlertOnly is False or 
                  self.event_dict[evID]['alert'] )):
                threshold_exceeded = True

            difftime = ed['tsobject'] - \
                self.event_dict[evID]['updates'][prefindex]['tsobject']
            ed['difftopref'] = difftime.length()
            ed['difftopref'] += self.event_dict[evID]['updates'][prefindex]['diff']
            
            formatted_params_point_src = {
                f"{ed['difftopref']:6.2f}",
                f"{ed['type']:4s}",
                f"{mag:4.2f}", 
                f"{ed['lat']:6.2f}", 
                f"{ed['lon']:7.2f}", 
                f"{ed['depth']:6.2f}", 
                f"{ed['ot']:s}", 
                f"{ed['likelihood']:4.2f}" if 'likelihood' in ed else "    ",
                f"{ed['nstorg']:3d}",
                f"{ed['nstmag']:3s}", 
                f"{ed['author'][:9]:9s}", 
                f"{ed['ts']:s}", 
                f"{ed['diff']:6.2f}"
            }
            point_src_updates.append("|".join(formatted_params_point_src))
            
            if ed['centroid_lat'] is not None and ed['centroid_lon'] is not None:
                formatted_params_finite_fault = {
                    f"{ed['difftopref']:6.2f}",
                    f"{ed['type']:4s}",
                    f"{mag:4.2f}", 
                    f"{ed['centroid_lat']:6.2f}", 
                    f"{ed['centroid_lon']:7.2f}", 
                    f"{ed['depth']:6.2f}", 
                    f"{ed['ot']:s}", 
                    f"{ed['likelihood']:4.2f}" if 'likelihood' in ed else "    ",
                    f"{ed['nstorg']:3d}",
                    f"{ed['nstmag']:3s}", 
                    f"{ed['rupture-strike']:4d}" if 'rupture-strike' in ed else "    ", 
                    f"{ed['rupture-length']:5.2f}" if 'rupture-length' in ed else "     ", 
                    f"{ed['author'][:9]:9s}", 
                    f"{ed['ts']:s}", 
                    f"{ed['diff']:6.2f}"
                }
                finite_fault_updates.append("|".join(formatted_params_finite_fault))

            if ed['difftopref'] < self.event_dict[evID]['diff']:
                self.event_dict[evID]['diff'] = ed['difftopref']
        report_pt_src = self.report_head_point_src + "\n".join(point_src_updates)
        report_ff = ""
        if len(finite_fault_updates) > 0:
            report_ff = self.report_head_finite_fault + "\n".join(finite_fault_updates)
        report = "\n".join((report_pt_src, report_ff))

        if self.storeReport:
            self.event_dict[evID]['report'] = report
            if not os.path.isdir(self.report_directory):
                os.makedirs(self.report_directory)
            f = open(os.path.join(self.report_directory,
                                  '%s_report.txt' % evID.replace('/', '_')), 'w')
            f.writelines(self.event_dict[evID]['report'])
            f.close()
        self.event_dict[evID]['type'] = ed['type']
        self.event_dict[evID]['magnitude'] = ed['magnitude']
        seiscomp.logging.info("\n" + report)
        if self.sendemail and threshold_exceeded:
            self.sendMail(self.event_dict[evID], evID)
        self.event_dict[evID]['published'] = True
