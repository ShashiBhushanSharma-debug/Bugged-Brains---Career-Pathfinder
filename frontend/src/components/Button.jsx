export default function Button({
  as = 'button',
  variant = 'primary',
  size = 'md',
  icon: Icon,
  iconPosition = 'right',
  children,
  className = '',
  ...rest
}) {
  const Tag = as;
  const classes = [
    'btn',
    variant === 'primary' && 'btn-primary',
    variant === 'secondary' && 'btn-secondary',
    variant === 'ghost' && 'btn-ghost',
    size === 'sm' && 'btn-sm',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <Tag className={classes} {...rest}>
      {Icon && iconPosition === 'left' && <Icon size={16} strokeWidth={2} />}
      {children}
      {Icon && iconPosition === 'right' && <Icon size={16} strokeWidth={2} />}
    </Tag>
  );
}