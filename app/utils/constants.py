"""Constants for the County Portal application"""                             
                                                                                  
    # User Roles (matching your existing roles in _init_.py)                    
class UserRoles:                                                              
    SUPER_ADMIN = 'super_admin'                                               
    STAFF = 'staff'                                                           
    CITIZEN = 'citizen'                                                       
    GUEST = 'guest'                                                           
                                                                                  
    # Status choices for future permit applications                               
class PermitStatus:                                                           
    DRAFT = 'draft'                                                           
    SUBMITTED = 'submitted'                                                   
    UNDER_REVIEW = 'under_review'                                             
    APPROVED = 'approved'                                                     
    REJECTED = 'rejected'                                                     
    EXPIRED = 'expired'