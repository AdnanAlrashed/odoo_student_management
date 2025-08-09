from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StudentResult(models.Model):
    _name = 'student_management.student_result'
    _description = 'Student Academic Result'
    _order = 'student_id, subject_id'
    _rec_name = 'display_name'

    student_id = fields.Many2one(
        'student_management.student',
        string='Student',
        required=True,
        ondelete='cascade',
        help='Student for whom the result is recorded'
    )
    subject_id = fields.Many2one(
        'student_management.subject',
        string='Subject',
        required=True,
        ondelete='cascade',
        help='Subject for which the result is recorded'
    )
    
    # Marks and Grades
    subject_exam_marks = fields.Float(
        string='Exam Marks',
        default=0.0,
        help='Marks obtained in the subject examination'
    )
    subject_assignment_marks = fields.Float(
        string='Assignment Marks',
        default=0.0,
        help='Marks obtained in subject assignments'
    )
    max_exam_marks = fields.Float(
        string='Maximum Exam Marks',
        default=100.0,
        help='Maximum marks for the examination'
    )
    max_assignment_marks = fields.Float(
        string='Maximum Assignment Marks',
        default=100.0,
        help='Maximum marks for assignments'
    )
    
    # Computed fields
    total_marks = fields.Float(
        string='Total Marks',
        compute='_compute_total_marks',
        store=True,
        help='Total marks obtained (exam + assignment)'
    )
    max_total_marks = fields.Float(
        string='Maximum Total Marks',
        compute='_compute_max_total_marks',
        store=True,
        help='Maximum total marks possible'
    )
    percentage = fields.Float(
        string='Percentage',
        compute='_compute_percentage',
        store=True,
        help='Percentage obtained'
    )
    grade = fields.Char(
        string='Grade',
        compute='_compute_grade',
        store=True,
        help='Grade based on percentage'
    )
    grade_point = fields.Float(
        string='Grade Point',
        compute='_compute_grade_point',
        store=True,
        help='Grade point based on percentage'
    )
    status = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('absent', 'Absent')
    ], string='Status', compute='_compute_status', store=True)
    
    # Additional Information
    exam_date = fields.Date(
        string='Exam Date',
        help='Date of the examination'
    )
    semester = fields.Integer(
        string='Semester',
        help='Semester for which the result is recorded'
    )
    academic_year = fields.Char(
        string='Academic Year',
        help='Academic year for the result'
    )
    remarks = fields.Text(
        string='Remarks',
        help='Additional remarks about the result'
    )
    
    # Related fields
    course_id = fields.Many2one(
        'student_management.course',
        string='Course',
        related='student_id.course_id',
        store=True,
        readonly=True
    )
    session_year_id = fields.Many2one(
        'student_management.session_year',
        string='Session Year',
        related='student_id.session_year_id',
        store=True,
        readonly=True
    )
    staff_id = fields.Many2one(
        'student_management.staff',
        string='Subject Teacher',
        related='subject_id.staff_id',
        store=True,
        readonly=True
    )
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('student_id', 'subject_id', 'total_marks', 'grade')
    def _compute_display_name(self):
        for record in self:
            if record.student_id and record.subject_id:
                record.display_name = f"{record.student_id.name} - {record.subject_id.subject_name} ({record.grade or 'N/A'})"
            else:
                record.display_name = "New Result"

    @api.depends('subject_exam_marks', 'subject_assignment_marks')
    def _compute_total_marks(self):
        for record in self:
            record.total_marks = record.subject_exam_marks + record.subject_assignment_marks

    @api.depends('max_exam_marks', 'max_assignment_marks')
    def _compute_max_total_marks(self):
        for record in self:
            record.max_total_marks = record.max_exam_marks + record.max_assignment_marks

    @api.depends('total_marks', 'max_total_marks')
    def _compute_percentage(self):
        for record in self:
            if record.max_total_marks > 0:
                record.percentage = (record.total_marks / record.max_total_marks) * 100
            else:
                record.percentage = 0.0

    @api.depends('percentage')
    def _compute_grade(self):
        for record in self:
            percentage = record.percentage
            if percentage >= 90:
                record.grade = 'A+'
            elif percentage >= 80:
                record.grade = 'A'
            elif percentage >= 70:
                record.grade = 'B+'
            elif percentage >= 60:
                record.grade = 'B'
            elif percentage >= 50:
                record.grade = 'C+'
            elif percentage >= 40:
                record.grade = 'C'
            elif percentage >= 35:
                record.grade = 'D'
            else:
                record.grade = 'F'

    @api.depends('percentage')
    def _compute_grade_point(self):
        for record in self:
            percentage = record.percentage
            if percentage >= 90:
                record.grade_point = 4.0
            elif percentage >= 80:
                record.grade_point = 3.7
            elif percentage >= 70:
                record.grade_point = 3.3
            elif percentage >= 60:
                record.grade_point = 3.0
            elif percentage >= 50:
                record.grade_point = 2.7
            elif percentage >= 40:
                record.grade_point = 2.3
            elif percentage >= 35:
                record.grade_point = 2.0
            else:
                record.grade_point = 0.0

    @api.depends('percentage')
    def _compute_status(self):
        for record in self:
            if record.percentage >= 35:  # Passing percentage
                record.status = 'pass'
            elif record.total_marks == 0 and record.subject_exam_marks == 0 and record.subject_assignment_marks == 0:
                record.status = 'absent'
            else:
                record.status = 'fail'

    @api.constrains('subject_exam_marks', 'max_exam_marks')
    def _check_exam_marks(self):
        for record in self:
            if record.subject_exam_marks < 0:
                raise ValidationError("Exam marks cannot be negative.")
            if record.max_exam_marks <= 0:
                raise ValidationError("Maximum exam marks must be greater than 0.")
            if record.subject_exam_marks > record.max_exam_marks:
                raise ValidationError("Exam marks cannot exceed maximum exam marks.")

    @api.constrains('subject_assignment_marks', 'max_assignment_marks')
    def _check_assignment_marks(self):
        for record in self:
            if record.subject_assignment_marks < 0:
                raise ValidationError("Assignment marks cannot be negative.")
            if record.max_assignment_marks <= 0:
                raise ValidationError("Maximum assignment marks must be greater than 0.")
            if record.subject_assignment_marks > record.max_assignment_marks:
                raise ValidationError("Assignment marks cannot exceed maximum assignment marks.")

    @api.constrains('student_id', 'subject_id', 'semester', 'academic_year')
    def _check_unique_result(self):
        for record in self:
            domain = [
                ('id', '!=', record.id),
                ('student_id', '=', record.student_id.id),
                ('subject_id', '=', record.subject_id.id)
            ]
            if record.semester:
                domain.append(('semester', '=', record.semester))
            if record.academic_year:
                domain.append(('academic_year', '=', record.academic_year))
            
            existing = self.search(domain)
            if existing:
                raise ValidationError(
                    f"Result for {record.student_id.name} in {record.subject_id.subject_name} "
                    f"for this semester/academic year already exists."
                )

    @api.model
    def get_student_result_summary(self, student_id, semester=None, academic_year=None):
        """Get result summary for a student"""
        domain = [('student_id', '=', student_id)]
        
        if semester:
            domain.append(('semester', '=', semester))
        if academic_year:
            domain.append(('academic_year', '=', academic_year))
        
        results = self.search(domain)
        
        if not results:
            return {}
        
        total_subjects = len(results)
        total_marks_obtained = sum(results.mapped('total_marks'))
        total_max_marks = sum(results.mapped('max_total_marks'))
        overall_percentage = (total_marks_obtained / total_max_marks * 100) if total_max_marks > 0 else 0
        
        # Calculate GPA
        total_grade_points = sum(results.mapped('grade_point'))
        gpa = total_grade_points / total_subjects if total_subjects > 0 else 0
        
        # Count by status
        passed = len(results.filtered(lambda r: r.status == 'pass'))
        failed = len(results.filtered(lambda r: r.status == 'fail'))
        absent = len(results.filtered(lambda r: r.status == 'absent'))
        
        summary = {
            'total_subjects': total_subjects,
            'total_marks_obtained': total_marks_obtained,
            'total_max_marks': total_max_marks,
            'overall_percentage': overall_percentage,
            'gpa': gpa,
            'passed_subjects': passed,
            'failed_subjects': failed,
            'absent_subjects': absent,
            'results': results.read(['subject_id', 'total_marks', 'percentage', 'grade', 'status'])
        }
        
        return summary

    @api.model
    def get_class_result_summary(self, course_id, subject_id=None, semester=None, academic_year=None):
        """Get result summary for a class/course"""
        domain = [('course_id', '=', course_id)]
        
        if subject_id:
            domain.append(('subject_id', '=', subject_id))
        if semester:
            domain.append(('semester', '=', semester))
        if academic_year:
            domain.append(('academic_year', '=', academic_year))
        
        results = self.search(domain)
        
        if not results:
            return {}
        
        total_students = len(results.mapped('student_id'))
        average_percentage = sum(results.mapped('percentage')) / len(results) if results else 0
        
        # Grade distribution
        grade_distribution = {}
        for grade in ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D', 'F']:
            count = len(results.filtered(lambda r: r.grade == grade))
            grade_distribution[grade] = count
        
        # Status distribution
        passed = len(results.filtered(lambda r: r.status == 'pass'))
        failed = len(results.filtered(lambda r: r.status == 'fail'))
        absent = len(results.filtered(lambda r: r.status == 'absent'))
        
        summary = {
            'total_students': total_students,
            'total_results': len(results),
            'average_percentage': average_percentage,
            'pass_rate': (passed / len(results) * 100) if results else 0,
            'grade_distribution': grade_distribution,
            'status_distribution': {
                'passed': passed,
                'failed': failed,
                'absent': absent
            }
        }
        
        return summary



