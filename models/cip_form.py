from odoo import models, fields, api, _


class PaymentModelExcel(models.Model):
    _inherit = 'payment.request'

    source_type = fields.Selection(
        selection_add=[('excel', 'Excel')], ondelete={'excel': 'cascade'}, string="Source Type",
    )
    excel_source = fields.Many2one('logic.cip.form', string="Excel Source")


class CipForm(models.Model):
    _name = 'logic.cip.form'
    _description = 'Cip Form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    batch_id = fields.Many2one('logic.base.batch', string='Batch', required=True)
    branch = fields.Many2one('logic.base.branches', related='batch_id.branch_id', string='Branch')
    date = fields.Date('Date', default=lambda self: fields.Date.context_today(self))
    batch_strength = fields.Integer(string="Strength",compute = "_compute_batch_strength")
    cip_avg_attendance = fields.Float(string="Average CIP Attendance",compute="_compute_cip_avg_attendance")
    excel_avg_attendance = fields.Float(string="Average Excel Attendance",compute="_compute_excel_avg_attendance")
    digital_support_received = fields.Boolean(string='Digital Support Received')
    rating = fields.Selection(
        selection=[('0', 'No rating'), ('1', 'Very Poor'), ('2', 'Poor'), ('3', 'Average'), ('4', 'Good'),
                   ('5', 'Very Good')], string="Rating", default='0')

    def _compute_excel_avg_attendance(self):
        for record in self:
            if record.attendance_excel_ids:
                total_attendance = 0
                for excel_rec in record.attendance_excel_ids:
                    if record.day_one_date:
                        if excel_rec.day_one_attendance=='full_day':
                            total_attendance+=1
                        elif excel_rec.day_one_attendance=="half_day":
                            total_attendance+=0.5
                    if record.day_two_date:
                        if excel_rec.day_two_attendance=='full_day':
                            total_attendance+=1
                        elif excel_rec.day_two_attendance=="half_day":
                            total_attendance+=0.5
                    if record.day_three_date:

                        if excel_rec.day_three_attendance=='full_day':
                            total_attendance+=1
                        elif excel_rec.day_three_attendance=="half_day":
                            total_attendance+=0.5
                if record.day_one_date and record.day_two_date and record.day_three_date:
                    record.excel_avg_attendance = total_attendance/3
                elif record.day_one_date and record.day_two_date:
                    record.excel_avg_attendance = total_attendance/2
                else:
                    record.excel_avg_attendance = total_attendance
            else:
                record.excel_avg_attendance = 0

    def _compute_cip_avg_attendance(self):
        for record in self:
            if record.cip_ids:
                total_attendance = 0
                for cip_rec in record.cip_ids:
                    if record.cip_day_one:
                        if cip_rec.day_one_cip_attendance=='full_day':
                            total_attendance+=1
                        elif cip_rec.day_one_cip_attendance=="half_day":
                            total_attendance+=0.5
                    if record.cip_day_two:
                        if cip_rec.day_two_cip_attendance=='full_day':
                            total_attendance+=1
                        elif cip_rec.day_two_cip_attendance=="half_day":
                            total_attendance+=0.5
                    if record.cip_day_three:

                        if cip_rec.day_three_cip_attendance=='full_day':
                            total_attendance+=1
                        elif cip_rec.day_three_cip_attendance=="half_day":
                            total_attendance+=0.5
                if record.cip_day_one and record.cip_day_two and record.cip_day_three:
                    record.cip_avg_attendance = total_attendance/3
                elif record.cip_day_one and record.cip_day_two:
                    record.cip_avg_attendance = total_attendance/2
                else:
                    record.cip_avg_attendance = total_attendance
            else:
                record.cip_avg_attendance = 0

    @api.depends('batch_id')
    def _compute_batch_strength(self):
        for record in self:
            if record.batch_id:
                record.batch_strength = self.env['logic.students'].search_count([('batch_id','=',record.batch_id.id)])    
            else:
                record.batch_strength = 0


    
            
    type_of_training = fields.Selection([
        ('cip', 'CIP'), ('excel', 'Excel'),
    ], string='Type of Training')

    state = fields.Selection([
        ('draft', 'Draft'), ('scheduled', 'Scheduled'), ('excel_started', 'Excel Started'),
        ('excel_completed', 'Excel Completed'), ('cip', 'CIP'), ('cip_started', 'CIP Started'), ('project', 'Project'),
        ('certificate', 'Certificate'), ('completed', 'Completed'),
    ], default='draft', string="Status")
    cip_ids = fields.One2many('logic.cip.attendance', 'cip_id', string='Attendance')
    day_one_date = fields.Date('Day One')
    day_two_date = fields.Date('Date Two')
    day_three_date = fields.Date('Date Three')
    excel_trainer = fields.Many2one('res.users', string='Excel Trainer', required=True)
    excel_record_ids = fields.One2many('excel.faculty.record', 'excel_faculty_id', string='Excel Record')
    coordinator_id = fields.Many2one('res.users', string='Coordinator', related='batch_id.academic_coordinator')
    attendance_excel_ids = fields.One2many('excel.students.attendance', 'students_excel_id', string='Attendance')
    programme_coord_id = fields.Many2one('res.users', string='Programme Coordinator',
                                         default=lambda self: self.env.user)

    # cip days
    cip_day_one = fields.Date('Day One')
    cip_day_two = fields.Date('Day Two')
    cip_day_three = fields.Date('Day Three')
    cip_day_four = fields.Date('Day Four')
    trainer_one = fields.Char('Trainer')
    trainer_two = fields.Char('Trainer')
    trainer_three = fields.Char('Trainer')
    trainer_four = fields.Char('Trainer')

    def action_submit(self):
        self.activity_schedule('logic_cip.mail_cip_activity', user_id=self.coordinator_id.id,
                               date_deadline=self.day_one_date,
                               note=f'Excel reminder.')
        self.state = 'scheduled'

    @api.onchange('batch_id')
    def onchange_students_attendance(self):
        print(self.batch_id, 'batch_id')
        students = self.env['logic.students'].search([('batch_id', '=', self.batch_id.id)])
        abc = []
        unlink_commands = [(3, child.id) for child in self.attendance_excel_ids]
        self.write({'attendance_excel_ids': unlink_commands})

        for i in students:
            res_list = {
                'student_name': i.name,
                'student_id': i.id,

            }
            abc.append((0, 0, res_list))
            print(abc, 'abc')
        self.attendance_excel_ids = abc

    def action_start(self):
        students = self.env['logic.students'].search([('batch_id', '=', self.batch_id.id)])
        abc = []
        unlink_commands = [(3, child.id) for child in self.cip_ids]
        self.write({'cip_ids': unlink_commands})

        for i in students:
            res_list = {
                'name': i.name,
                'student_id': i.id,

            }
            abc.append((0, 0, res_list))
        self.cip_ids = abc
        for rec in self.cip_ids:
            rec.state = 'excel_started'
        self.state = 'excel_started'
        activity = self.env['mail.activity'].search([('res_id', '=', self.id), (
            'activity_type_id', '=', self.env.ref('logic_cip.mail_cip_activity').id)])
        activity.action_feedback('CIP Started')

    def action_project(self):
        for rec in self.cip_ids:
            rec.state = 'project'
        self.state = 'project'
        self.cip_ids.project_submit = True

    def action_excel_completed(self):
        for rec in self.cip_ids:
            rec.state = 'excel_completed'
        self.state = 'excel_completed'

    def action_excel_done(self):
        self.env['payment.request'].sudo().create({
            'source_type': 'excel',
            'source_user': self.excel_trainer.id,
            'excel_source': self.id,
            'amount': self.payment_total,
        })
        for rec in self.cip_ids:
            rec.state = 'cip'
        self.state = 'cip'
        students = self.env['logic.students'].search([('batch_id', '=', self.batch_id.id)])
        for i in students:
            print(i, 'i')
            for rec in self.attendance_excel_ids:
                print(rec.student_id, 'rec')
                print(i.id, 'id')
                if rec.student_id == i.id:
                    print('ya')
                    if self.day_one_date:
                        i.day_one_excel = self.day_one_date
                        i.day_one_excel_attendance = rec.day_one_attendance
                    if self.day_two_date:
                        i.day_two_excel = self.day_two_date
                        i.day_two_excel_attendance = rec.day_two_attendance
                    if self.day_three_date:
                        i.day_three_excel = self.day_three_date
                        i.day_three_excel_attendance = rec.day_three_attendance
                else:
                    print('na')

    def action_cip_started(self):
        for rec in self.cip_ids:
            rec.state = 'cip_started'
        self.state = 'cip_started'

    def action_certificate(self):
        for rec in self.cip_ids:
            rec.state = 'certificate'
        self.state = 'certificate'
        self.cip_ids.certificate_submit = True


    def action_completed(self):
        for rec in self.cip_ids:
            rec.state = 'completed'
        self.state = 'completed'
        students = self.env['logic.students'].search([('batch_id', '=', self.batch_id.id)])
        for i in students:
            print(i, 'i')
            for rec in self.cip_ids:
                print(rec.student_id, 'rec')
                print(i.id, 'id')
                if rec.student_id == i.id:
                    print('ya')
                    if self.cip_day_one:
                        i.day_one_cip = self.cip_day_one
                        i.day_one_cip_attendance = rec.day_one_cip_attendance
                    if self.cip_day_two:
                        i.day_two_cip = self.cip_day_two
                        i.day_two_cip_attendance = rec.day_two_cip_attendance
                    if self.cip_day_three:
                        i.day_three_cip = self.cip_day_three
                        i.day_three_cip_attendance = rec.day_three_cip_attendance
                    if self.cip_day_four:
                        i.day_four_cip = self.cip_day_four
                        i.day_four_cip_attendance = rec.day_four_cip_attendance
                else:
                    print('na')

    def action_excel_completed_faculty(self):
        for rec in self.cip_ids:
            rec.state = 'excel_completed'
        self.state = 'excel_completed'

    def _compute_display_name(self):
        for rec in self:
            if rec.name and rec.batch_id:
                rec.display_name = rec.name + ' - ' + rec.batch_id.name
            elif rec.batch_id:
                rec.display_name = rec.batch_id.name + ' - CIP'
            else:
                rec.display_name = 'CIP'

    display_name = fields.Char(compute='_compute_display_name', string='Display Name', store=True)

    @api.depends('excel_record_ids.total_duration')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        total = 0
        for record in self.excel_record_ids:
            total += record.total_duration
        self.update({
            'excel_payment_total_duration': total,

        })

    excel_payment_total_duration = fields.Float(string='Total Duration', compute='_amount_all', store=True)

    @api.depends('excel_record_ids.total_duration')
    def _compute_total_record(self):
        total = 0
        payment = self.env['excel.faculty.payment'].search([('faculty_id', '=', self.excel_trainer.id)])
        print(payment.excel_payment, 'ui')
        total += payment.excel_payment * self.excel_payment_total_duration
        self.update({
            'payment_total': total,
        })

    payment_total = fields.Float(string='Total Payment', compute='_compute_total_record', store=True)

    @api.onchange('day_one_date', 'day_two_date', 'day_three_date', 'day_four_date')
    def _onchange_excel_date_one_test(self):
        print('yes')
        if self.day_one_date:
            self.attendance_excel_ids.day_one_check = True
            self.attendance_excel_ids.day_one_attendance = "full_day"
        else:
            self.attendance_excel_ids.day_one_check = False
            self.attendance_excel_ids.day_one_attendance = False

        if self.day_two_date:
            self.attendance_excel_ids.day_two_check = True
            self.attendance_excel_ids.day_two_attendance = "full_day"

        else:
            self.attendance_excel_ids.day_two_check = False
            self.attendance_excel_ids.day_two_attendance = False

        if self.day_three_date:
            self.attendance_excel_ids.day_three_check = True
            self.attendance_excel_ids.day_three_attendance = "full_day"

        else:
            self.attendance_excel_ids.day_three_check = False
            self.attendance_excel_ids.day_three_attendance = False


    @api.onchange('cip_day_one', 'cip_day_two', 'cip_day_three')
    def _onchange_cip_date_attendance(self):
        print('yes')
        if self.cip_day_one:
            self.cip_ids.day_one_check = True
            self.cip_ids.day_one_cip_attendance = "full_day"
        else:
            self.cip_ids.day_one_check = False
            self.cip_ids.day_one_cip_attendance = False

        if self.cip_day_two:
            self.cip_ids.day_two_check = True
            self.cip_ids.day_two_cip_attendance = "full_day"

        else:
            self.cip_ids.day_two_check = False
            self.cip_ids.day_two_cip_attendance = False

        if self.cip_day_three:
            self.cip_ids.day_three_check = True
            self.cip_ids.day_three_cip_attendance = "full_day"

        else:
            self.cip_ids.day_three_check = False
            self.cip_ids.day_three_cip_attendance = False

        if self.cip_day_four:
            self.cip_ids.day_four_check = True
            self.cip_ids.day_four_cip_attendance = "full_day"

        else:
            self.cip_ids.day_four_check = False
            self.cip_ids.day_four_cip_attendance = False



class ExcelClassAttendance(models.Model):
    _name = 'excel.students.attendance'

    student_name = fields.Char('Student Name')
    day_one_attendance = fields.Selection([('full_day', 'Full Day'), ('half_day', 'Half Day'), ('absent', 'Absent')],
                                          'Day 1')
    day_two_attendance = fields.Selection([('full_day', 'Full Day'), ('half_day', 'Half Day'), ('absent', 'Absent')],
                                          'Day 2')
    day_three_attendance = fields.Selection([('full_day', 'Full Day'), ('half_day', 'Half Day'), ('absent', 'Absent')],
                                            'Day 3')
    
    stud_attendance = fields.Float(string="Attendance",compute="_compute_stud_attendance")

    def _compute_stud_attendance(self):
        for record in self:
            total_present = 0
            if record.day_one_attendance=="full_day":
                total_present+=1
            elif record.day_one_attendance=="half_day":
                total_present+=0.5

            if record.day_two_attendance=="full_day":
                total_present+=1
            elif record.day_two_attendance=="half_day":
                total_present+=0.5

            if record.day_three_attendance=="full_day":
                total_present+=1
            elif record.day_three_attendance=="half_day":
                total_present+=0.5
            record.stud_attendance = total_present

    # @api.onchange('day_one_check')
    # def on_day_one_check_change(self):
    #     for record in self:
    #         if record.day_one_check:
    #             record.day_one_attendance = 'full_day'
    #         else:
    #             record.day_one_attendance = False

    # @api.onchange('day_two_check')
    # def on_day_two_check_change(self):
    #     for record in self:
    #         if record.day_two_check:
    #             record.day_two_attendance = 'full_day'
    #         else:
    #             record.day_two_attendance = False

    # @api.onchange('day_three_check')
    # def on_day_three_check_change(self):
    #     for record in self:
    #         if record.day_three_check:
    #             record.day_three_attendance = 'full_day'
    #         else:
    #             record.day_three_attendance = False

    students_excel_id = fields.Many2one('logic.cip.form')
    student_id = fields.Integer()
    day_one_check = fields.Boolean('Day One')
    day_two_check = fields.Boolean('Day Two')
    day_three_check = fields.Boolean('Day Three')
