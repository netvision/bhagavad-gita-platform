export const learningRoles = ['student', 'teacher', 'content_admin', 'super_admin'];
export const adminRoles = ['content_admin', 'super_admin'];

export function roleCanAccess(userRole, allowedRoles = []) {
  return allowedRoles.includes(userRole);
}

export function defaultRouteForRole(role) {
  return adminRoles.includes(role) ? '/admin' : '/learn';
}
