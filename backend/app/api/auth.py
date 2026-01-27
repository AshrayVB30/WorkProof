from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from app.models.user import User
from app.utils.encryption import hash_password, verify_password, create_access_token, create_refresh_token, verify_token
from app.utils.validators import validate_email, validate_password_strength
from app.schemas.user import UserCreate, UserLogin, TokenResponse, UserResponse, TokenRefresh
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate
):
    """
    Register a new user (admin or employee)
    Note: In production, only admins should be able to create new users
    """
    # Validate email
    if not validate_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Check if user already exists
    existing_user = await User.find_one(User.email == user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if employee_id is unique (if provided)
    if user_data.employee_id:
        existing_employee = await User.find_one(User.employee_id == user_data.employee_id)
        if existing_employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID already exists"
            )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        expected_daily_hours=user_data.expected_daily_hours,
        department=user_data.department,
        employee_id=user_data.employee_id
    )
    
    await new_user.insert()
    
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin
):
    """Authenticate user and return JWT tokens"""
    # Find user by email
    user = await User.find_one(User.email == credentials.email)
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    await user.save()
    
    # Create tokens
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: TokenRefresh
):
    """Refresh access token using refresh token"""
    from beanie import PydanticObjectId
    
    # Verify refresh token
    payload = verify_token(data.refresh_token, token_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user
    user_id = payload.get("sub")
    user = await User.get(PydanticObjectId(user_id))
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role.value}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user information"""
    return current_user


@router.get("/consent")
async def get_consent_status(
    current_user: User = Depends(get_current_user)
):
    """Check if the user has given consent"""
    return {"consent_accepted": current_user.consent_accepted}


@router.post("/consent")
async def give_consent(
    current_user: User = Depends(get_current_user)
):
    """Employee gives consent for activity tracking"""
    current_user.consent_accepted = True
    await current_user.save()
    return {"message": "Consent successfully given", "consent_accepted": True}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout user
    Note: With JWT, actual logout is handled client-side by removing the token
    This endpoint is for logging purposes
    """
    return {"message": "Successfully logged out"}
